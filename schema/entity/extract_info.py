from typing import Optional
from pydantic import BaseModel, ConfigDict


class ExtractInfoEntity(BaseModel):
    """抽取结果实体：与 `database.models.ExtractInfo` 对应。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    content_id: int
    content_type: int
    content_source: str
    city_entity: Optional[str] = None
    industry_entity: Optional[str] = None
    figure_entity: Optional[str] = None
    three_emo: Optional[str] = None
    six_emo: Optional[str] = None
    summary: Optional[str] = None
    clustering: Optional[str] = None
    view: Optional[str] = None
    hot_topics: Optional[str] = None
    # 统一使用空串，避免 None 映射错误
    domain: str = ""
    posts_topics: Optional[str] = None

    def to_dict(self) -> dict:
        return self.model_dump()