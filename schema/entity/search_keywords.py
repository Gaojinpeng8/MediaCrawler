from pydantic import BaseModel, ConfigDict


class SearchKeywordsEntity(BaseModel):
    """search_keywords 实体：与 MySQL 表 `search_keywords` 对应。

    字段含义：
    - id: 主键，自增
    - create_time: 创建时间（毫秒时间戳）
    - plan_id: 监控方案ID（与 monitor_plan.plan_id 对齐为 BIGINT）
    - keywords: 搜索的关键词
    """

    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    create_time: int
    plan_id: int
    keywords: str
    # 运行态字段：用于记录最近一次更新的时间与间隔，不入库时可为空
    last_update_time: int | None = None
    update_interval: int | None = None

    def to_dict(self) -> dict:
        return self.model_dump()