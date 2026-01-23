from typing import Optional
from pydantic import BaseModel, ConfigDict


class HistoryUpdateEntity(BaseModel):
    """历史更新记录实体：与 `database.models.HistoryUpdate` 对应。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    content_type: Optional[int] = None
    content_id: int
    content_viewd_cnt: Optional[int] = None
    content_liked_cnt: Optional[int] = None
    content_collected_cnt: Optional[int] = None
    content_comment_cnt: Optional[int] = None
    content_shared_cnt: Optional[int] = None
    emotion_negative_cnt: Optional[int] = None
    emotion_positive_cnt: Optional[int] = None
    emotion_neutral_cnt: Optional[int] = None

    def to_dict(self) -> dict:
        return self.model_dump()