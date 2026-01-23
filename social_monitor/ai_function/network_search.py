import json
from typing import List, Dict, Optional

try:
    from baidusearch.baidusearch import search  # type: ignore
except ImportError:
    raise ImportError("`baidusearch` 未安装。请执行 `pip install baidusearch`")

from .base_function_ai import BaseFunctionAI, OpenAIChatClient


class BaiduNetworkSearchAI(BaseFunctionAI):
    """
    基于 BaiduSearch 的网络检索类，继承 BaseFunctionAI。

    execute(query) 返回 JSON 字符串，包含 title/url/abstract/rank 字段。
    """

    def __init__(
        self,
        config: Optional[object] = None,
        client: Optional[OpenAIChatClient] = None,
        num_results: int = 10,
    ):
        super().__init__(config=config, client=client)
        self.num_results = num_results

    def execute(self, query: str) -> str:
        """同步执行百度搜索并返回格式化 JSON 字符串"""
        try:
            results = search(keyword=query, num_results=self.num_results)
        except Exception as e:
            return json.dumps([{"error": str(e)}], indent=2, ensure_ascii=False)

        res: List[Dict[str, str]] = []
        for idx, item in enumerate(results, 1):
            res.append(
                {
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "abstract": item.get("abstract", ""),
                    "rank": str(idx),
                }
            )
        return json.dumps(res, indent=2, ensure_ascii=False)

    async def execute_async(self, query: str) -> str:
        """简单的异步封装：直接复用同步实现"""
        return self.execute(query)