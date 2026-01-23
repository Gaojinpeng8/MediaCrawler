from typing import Iterable, List, Optional

from media_crawler.database import models
from .entity.content import ContentEntity
from .entity.comment import CommentEntity
from .entity.hotlist import HotlistEntity
from .entity.extract_info import ExtractInfoEntity
from .entity.monitor_group import MonitorGroupEntity
from .entity.monitor_plan import MonitorPlanEntity
from .entity.user import UserEntity
from .entity.plan_content import PlanContentEntity
from .entity.history_update import HistoryUpdateEntity
from .entity.hot_topics import HotTopicsEntity
from .entity.forwarding import ForwardingEntity


class EntityFactory:
    """实体转换工厂：提供从 ORM 模型到 Pydantic 实体的转换。

    使用 Pydantic v2 的 `model_validate` 支持从属性加载。
    """

    @staticmethod
    def content_from_model(obj: models.Content) -> ContentEntity:
        return ContentEntity.model_validate(obj)

    @staticmethod
    def comment_from_model(obj: models.Comment) -> CommentEntity:
        return CommentEntity.model_validate(obj)

    @staticmethod
    def hotlist_from_model(obj: models.Hotlist) -> HotlistEntity:
        return HotlistEntity.model_validate(obj)

    @staticmethod
    def extract_info_from_model(obj: models.ExtractInfo) -> ExtractInfoEntity:
        return ExtractInfoEntity.model_validate(obj)

    @staticmethod
    def monitor_group_from_model(obj: models.MonitorGroup) -> MonitorGroupEntity:
        return MonitorGroupEntity.model_validate(obj)

    @staticmethod
    def monitor_plan_from_model(obj: models.MonitorPlan) -> MonitorPlanEntity:
        return MonitorPlanEntity.model_validate(obj)

    @staticmethod
    def user_from_model(obj: models.User) -> UserEntity:
        return UserEntity.model_validate(obj)

    @staticmethod
    def plan_content_from_model(obj: models.PlanContent) -> PlanContentEntity:
        return PlanContentEntity.model_validate(obj)

    @staticmethod
    def history_update_from_model(obj: models.HistoryUpdate) -> HistoryUpdateEntity:
        return HistoryUpdateEntity.model_validate(obj)

    @staticmethod
    def hot_topics_from_model(obj: models.HotTopics) -> HotTopicsEntity:
        return HotTopicsEntity.model_validate(obj)

    @staticmethod
    def forwarding_from_model(obj: models.Forwarding) -> ForwardingEntity:
        return ForwardingEntity.model_validate(obj)

    @staticmethod
    def contents_from_iter(objs: Iterable[models.Content]) -> List[ContentEntity]:
        return [ContentEntity.model_validate(o) for o in objs]

    @staticmethod
    def comments_from_iter(objs: Iterable[models.Comment]) -> List[CommentEntity]:
        return [CommentEntity.model_validate(o) for o in objs]

    @staticmethod
    def plan_contents_from_iter(objs: Iterable[models.PlanContent]) -> List[PlanContentEntity]:
        return [PlanContentEntity.model_validate(o) for o in objs]

    @staticmethod
    def history_updates_from_iter(objs: Iterable[models.HistoryUpdate]) -> List[HistoryUpdateEntity]:
        return [HistoryUpdateEntity.model_validate(o) for o in objs]

    @staticmethod
    def hot_topics_from_iter(objs: Iterable[models.HotTopics]) -> List[HotTopicsEntity]:
        return [HotTopicsEntity.model_validate(o) for o in objs]

    @staticmethod
    def forwardings_from_iter(objs: Iterable[models.Forwarding]) -> List[ForwardingEntity]:
        return [ForwardingEntity.model_validate(o) for o in objs]