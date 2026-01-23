from typing import Optional
from pydantic import BaseModel, ConfigDict


class HotlistEntity(BaseModel):
    """热榜实体：与 `database.models.Hotlist` 对应的传输对象。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    hot_title: str
    hot_time: int
    hot_rank: int
    hot_score: int
    hot_source: str
    hot_question_id: Optional[str] = None
    hot_desc: Optional[str] = None
    hot_question_answer_cnt: Optional[int] = None
    hot_question_url: Optional[str] = None
    hot_pic_url: Optional[str] = None
    hot_video_ids: Optional[str] = None

    def to_dict(self) -> dict:
        return self.model_dump()