from typing import Optional
from pydantic import BaseModel, ConfigDict


class HistoryEntity(BaseModel):
    """热度历史实体：与 `history` 表结构对齐的传输对象。"""

    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    search_keyword_id: int
    search_keyword: Optional[str] = None
    total_posts: int = 0
    total_views: int = 0
    total_likes: int = 0
    avg_views: int = 0
    avg_likes: int = 0
    positive_comments: int = 0
    negative_comments: int = 0
    neutral_comments: int = 0
    positive_posts: int = 0
    negative_posts: int = 0
    neutral_posts: int = 0
    hottest_post_id: Optional[str] = None
    hottest_comment_id: Optional[str] = None
    search_time: int
    create_time: int

    def to_dict(self) -> dict:
        """返回字典形式，便于序列化或日志输出。"""
        return self.model_dump()