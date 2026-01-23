from typing import Optional, Any, Dict, List
import os
import json
import config
from schema.entity.monitor_plan import MonitorPlanEntity
import re

try:
    from openai import OpenAI
except Exception as _e:  # 延迟在初始化时报错，便于导入不失败
    OpenAI = None  # type: ignore
    _import_exc = _e
    
def extract_json_result(results):
    pattern = r"```json\s*(.*?)\s*```"
    json_strings = re.findall(pattern, results, flags=re.S)
    if len(json_strings) == 0:
        return {}
    json_str = json_strings[0]
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError:
        return {}
    return data

class BaseSearch:
    
    def search(self, prompt: str, model: str = config.BAIDU_SEACH["model"], stream: bool = False) -> str:
        raise NotImplementedError("search 方法未实现")

    def search_init_monitor(self, monitor_plan: MonitorPlanEntity, time_range: str, nums: int) -> list[str]:
        prompt = """你是一个网上舆情收集的专家，目前有一个网上舆情的检测方案，你需要根据检测方案的内容去网上收集近期最新的一些热点事件，然后以关键词的形式给出。       
检测方案的名称: {monitor_name}
检测方案的关键词: {keywords}
时间要求: {time}
事件数量要求: {nums}

要求：
1. 请你基于现有的方案和关键词，进行一定的改写，然后去网上搜相关的热点事件。
2. 然后对搜索到的内容进行一定的过滤，例如需要满足时间要求等, 事件的需求尽量满足，如果不够的话就算了。
3. 给出的热点事件尽可能存在差异化，更全面的捕捉检测方案下面的事件，而不是集中在某几个事件上。
4. 最终经过分析之后以下面的格式返回结果:
```json
{{
    "hot_event_keywords": ["事件1","事件2",..]
}}
```
"""
        final_prompt = prompt.format(monitor_name=monitor_plan.plan_name, keywords=monitor_plan.keywords, time=time_range, nums=nums)        
        results =  self.search(messages=[{"role": "user", "content": final_prompt}])
        data = extract_json_result(results)
        if "hot_event_keywords" not in data:
            return []
        return data.get("hot_event_keywords", [])
    
    
class BAIDUSearch(BaseSearch):
    def __init__(self, api_key: Optional[str] = config.BAIDU_SEACH['api_key'], base_url: Optional[str] = config.BAIDU_SEACH["base_url"], default_headers: Optional[dict] = None):
        if OpenAI is None:
            raise ImportError("未安装 openai SDK，请先执行: pip3 install openai") from _import_exc  # type: ignore

        key = api_key or ""
        url = (base_url or config.BAIDU_SEACH["base_url"]).strip()
        self.client = OpenAI(api_key=key, base_url=url, default_headers=default_headers)

    def search(self, messages: List[Dict[str, Any]], model: str = config.BAIDU_SEACH["model"], stream: bool = False) -> str:
        resp = self.client.chat.completions.create(
            model=model,
            messages=messages,
            stream=stream,
        )
        # 非流式，直接返回文本内容
        return resp.choices[0].message.content
    
class KIMISearch(BaseSearch):
    def __init__(
        self,
        api_key: Optional[str] = config.KIMI_SEARCH['api_key'],
        base_url: Optional[str] = config.KIMI_SEARCH['base_url'],
        default_headers: Optional[dict] = None,
    ):
        if OpenAI is None:
            raise ImportError("未安装 openai SDK，请先执行: pip3 install openai") from _import_exc  # type: ignore

        key = api_key or os.environ.get("MOONSHOT_API_KEY") or config.KIMI_SEARCH.get("api_key", "")
        url = (base_url or config.KIMI_SEARCH['base_url']).strip()
        self.client = OpenAI(api_key=key, base_url=url, default_headers=default_headers)

    # search 工具具体实现：Moonshot 的 $web_search 只需原样返回参数
    def search_impl(self, arguments: Dict[str, Any]) -> Any:
        return arguments

    def chat(
        self,
        messages: List[Dict[str, Any]],
        model: str = "kimi-k2-turbo-preview",
        temperature: float = 0.6,
        max_tokens: int = 32768,
    ):
        completion = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=[
                {
                    "type": "builtin_function",
                    "function": {"name": "$web_search"},
                }
            ],
        )
        return completion.choices[0]

    def search(self, messages: List[Dict[str, Any]]) -> str:
        finish_reason = None
        choice = None
        while finish_reason is None or finish_reason == "tool_calls":
            choice = self.chat(messages)
            finish_reason = getattr(choice, "finish_reason", None)
            if finish_reason == "tool_calls":
                # 将 assistant 的 tool_calls 消息加入上下文，便于下一次请求理解意图
                messages.append(choice.message)
                for tool_call in getattr(choice.message, "tool_calls", []) or []:
                    tool_call_name = tool_call.function.name
                    tool_call_arguments = json.loads(tool_call.function.arguments)
                    if tool_call_name == "$web_search":
                        tool_result = self.search_impl(tool_call_arguments)
                    else:
                        tool_result = f"Error: unable to find tool by name '{tool_call_name}'"

                    # 将工具执行结果以 role=tool 的消息返回给模型
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": tool_call_name,
                            "content": json.dumps(tool_result),
                        }
                    )

        return choice.message.content if choice else ""

    def ask(self, query: str, system_prompt: str = "你是 Kimi。") -> str:
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query},
        ]
        return self.run(messages)
    
    