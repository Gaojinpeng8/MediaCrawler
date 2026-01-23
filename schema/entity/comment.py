from typing import Optional
from pydantic import BaseModel, ConfigDict


class CommentEntity(BaseModel):
    """评论实体：与 `database.models.Comment` 对应的传输对象。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    content_id: str
    comment_id: str
    # tables.sql 中为 varchar，允许 '0' 字符，改为字符串类型
    par_comment_id: str
    comment_crawl_time: int
    comment_time: int
    comment_desc: str
    sub_comment_cnt: int
    comment_liked_cnt: Optional[int] = None
    comment_ip: Optional[str] = None
    comment_user_id: str
    comment_user_nickname: str
    comment_user_gender: str
    comment_user_home: Optional[str] = None
    comment_source: str
    comment_pics: Optional[str] = None

    def to_dict(self) -> dict:
        return self.model_dump()