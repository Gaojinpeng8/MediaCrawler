from typing import Dict, Any
from pydantic import BaseModel, ConfigDict


class MonitorPlanEntity(BaseModel):
    """监控方案实体：与 `monitor_plan` 表结构对齐的传输对象。"""

    model_config = ConfigDict(from_attributes=True)

    plan_id: int
    group_id: int | None = None
    group_name: str | None = None
    plan_name: str | None = None
    keywords: str | None = None
    ignore_keywords: str | None = None
    platform: str | None = 'all'
    emotion: str | None = None
    topics: str | None = None
    domain: str | None = None
    monitor_time_interval: int
    last_update_time: int | None = None
    last_analysis_time: int | None = None
    monitor_time_range: int
    warning_interval: int
    warning_rate: float
    describe: str
    status: bool = True  # tinyint(1) 映射为 bool，默认 True
    # 与 DDL 对齐：使用毫秒级时间戳
    create_time: int

    def to_dict(self) -> dict:
        return self.model_dump()