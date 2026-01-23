"""实体模块包：存放所有 Pydantic 实体类。

该包仅承载实体定义，顶层 `media_crawler.schema.__init__` 负责统一导出，
以保证外部调用路径保持不变（`from media_crawler.schema import ...`）。
"""

__all__ = []