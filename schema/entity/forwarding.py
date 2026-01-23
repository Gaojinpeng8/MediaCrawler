from typing import Optional
from pydantic import BaseModel, ConfigDict


class ForwardingEntity(BaseModel):
    """转发关系实体：与 `database.models.Forwarding` 对应。"""

    model_config = ConfigDict(from_attributes=True)

    from_id: Optional[str] = None
    id: int
    to_id: str
    content_viewd_cnt: Optional[int] = None
    content_collected_cnt: Optional[int] = None
    content_shared_cnt: Optional[int] = None
    content_comment_cnt: Optional[int] = None
    content_liked_cnt: Optional[int] = None

    def to_dict(self) -> dict:
        return self.model_dump()