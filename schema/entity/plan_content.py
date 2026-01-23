from pydantic import BaseModel, ConfigDict


class PlanContentEntity(BaseModel):
    """方案内容关联实体：与 `database.models.PlanContent` 对应。"""

    model_config = ConfigDict(from_attributes=True)

    relation_id: int = None
    content_type: int = 2
    content_id: int
    status: int = 1
    plan_id: int
    keyword_id: str

    def to_dict(self) -> dict:
        return self.model_dump()