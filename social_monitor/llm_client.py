from openai import OpenAI
from typing import Optional, Dict, List, Any

class OpenAIChatClient:
    def __init__(
        self,
        api_key: str = "EMPTY",
        base_url: str = "http://localhost:8000/v1",
        default_model: Optional[str] = "/data/testmllm/models/Qwen/Qwen3-30B-A3B-Instruct-2507",
    ):
        """
        OpenAI 兼容客户端封装

        Args:
            api_key: vLLM 不校验 key，任意字符串即可
            base_url: 服务地址（与启动端口一致）
            default_model: 默认模型名称（不传则调用时必须显式指定）
        """
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.default_model = default_model

    def infer(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        temperature: Optional[float] = 0.6,
        top_p: Optional[float] = 0.9,
        top_k: Optional[int] = 6,
        max_tokens: Optional[int] = 16384,
        enable_thinking: bool = False,
        **kwargs
    ) -> str:
        """
        单次推理（messages 为标准 Chat 格式）

        Returns:
            模型返回的文本（choices[0].message.content）
        """
        use_model = model or self.default_model
        if not use_model:
            raise ValueError("必须提供模型名称：请传入 model 或在初始化时设置 default_model")
        # 采样参数
        params: Dict[str, Any] = {
            k: v for k, v in {
                "temperature": temperature,
                "top_p": top_p,
                "max_tokens": max_tokens,
                **kwargs,
            }.items() if v is not None
        }

        resp = self.client.chat.completions.create(
            model=use_model,
            messages=messages,
            **params,
            extra_body={"chat_template_kwargs": {"enable_thinking": enable_thinking}}
        )
        return {"content": resp.choices[0].message.content, "reasoning_content": resp.choices[0].message.reasoning_content}

    def batch_infer(
        self,
        batch_messages: List[List[Dict[str, Any]]],
        model: Optional[str] = None,
        temperature: Optional[float] = 0.6,
        top_p: Optional[float] = 0.9,
        top_k: Optional[int] = 6,
        max_tokens: Optional[int] = 16384,
        enable_thinking: bool = False,
        thread_num: int = 4,
        **kwargs
    ) -> List[str]:
        """
        批量推理（多个 messages 列表），支持多线程并发

        Args:
            thread_num: 并发线程数，默认 4

        Returns:
            文本结果列表（与输入批次顺序对应）
        """
        results = [None] * len(batch_messages)

        def _task(idx, messages):
            return idx, self.infer(messages, model, temperature, top_p, max_tokens, enable_thinking, **kwargs)

        with ThreadPoolExecutor(max_workers=thread_num) as executor:
            future_to_idx = {
                executor.submit(_task, idx, messages): idx
                for idx, messages in enumerate(batch_messages)
            }
            for future in as_completed(future_to_idx):
                idx, text = future.result()
                results[idx] = text

        return results