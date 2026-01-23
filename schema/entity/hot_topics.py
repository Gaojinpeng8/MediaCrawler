from typing import Optional
from pydantic import BaseModel, ConfigDict


class HotTopicsEntity(BaseModel):
    """热点主题实体：与 `database.models.HotTopics` 对应。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    content_type: Optional[int] = None
    content_id: Optional[int] = None
    status: Optional[int] = None

    def to_dict(self) -> dict:
        return self.model_dump()