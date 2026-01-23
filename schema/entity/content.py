from typing import Optional
from pydantic import BaseModel, ConfigDict


class ContentEntity(BaseModel):
    """内容实体：与 `database.models.Content` 对应的传输对象。
    仅用于业务层交互，避免直接依赖 ORM 模型。
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    hot_id: Optional[int] = None
    content_source: str
    content_id: str
    question_id: Optional[str] = None
    content_crawl_time: int
    content_title: Optional[str] = None
    # tables.sql 中 content_desc 为 text（允许 NULL），改为可选
    content_desc: Optional[str] = None
    content_time: int
    content_user_id: Optional[str] = None
    content_user_gender: int
    content_user_nickname: str
    content_user_home: Optional[str] = None
    content_viewd_cnt: Optional[int] = None
    # tables.sql 将 liked_cnt 定义为 bigint DEFAULT NULL
    content_liked_cnt: Optional[int] = None
    content_collected_cnt: Optional[int] = None
    content_comment_cnt: Optional[int] = None
    content_shared_cnt: Optional[int] = None
    content_ip: Optional[str] = None
    content_url: str
    content_emotion: Optional[str] = None
    content_pics: Optional[str] = None
    content_videos: Optional[str] = None
    content_musics: Optional[str] = None
    content_cover_url: Optional[str] = None

    def to_dict(self) -> dict:
        """返回字典形式，便于序列化或日志输出。"""
        return self.model_dump()