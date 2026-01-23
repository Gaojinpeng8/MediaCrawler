from typing import Optional
from pydantic import BaseModel, ConfigDict


class MonitorGroupEntity(BaseModel):
    """监控组实体：与 `database.models.MonitorGroup` 对应的传输对象。"""

    model_config = ConfigDict(from_attributes=True)

    group_id: int
    group_name: Optional[str] = None

    def to_dict(self) -> dict:
        return self.model_dump()