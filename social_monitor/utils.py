import datetime
import copy
import types

def _safe_deepcopy(value):
    """对配置值进行安全深拷贝：
    - JSON 原始类型直接返回
    - 容器类型深拷贝
    - 模块、函数、类、日志器等不可/不需要拷贝的对象保持引用
    - 其他对象尝试深拷贝，失败则保留原引用
    """
    if isinstance(value, (int, float, str, bool, type(None))):
        return value
    if isinstance(value, (list, dict, set, tuple)):
        return copy.deepcopy(value)
    if isinstance(value, types.ModuleType):
        return value
    # 避免对函数/类等对象做不必要的拷贝
    if callable(value) or isinstance(value, type):
        return value
    try:
        return copy.deepcopy(value)
    except Exception:
        return value

def clone_config(config_obj, **overrides):
    # 逐字段安全拷贝，避免 SimpleNamespace 内含模块对象导致 deepcopy 报错
    new_dict = {}
    for k, v in getattr(config_obj, "__dict__", {}).items():
        new_dict[k] = _safe_deepcopy(v)
    new_cfg = types.SimpleNamespace(**new_dict)
    for k, v in overrides.items():
        setattr(new_cfg, k, v)
    return new_cfg


def bigint_to_datetime(bigint_ts: int) -> datetime.datetime:
    """
    将 bigint 类型的时间戳（毫秒）转换为 datetime 对象
    :param bigint_ts: 毫秒级时间戳
    :return: datetime 对象
    """
    # 毫秒转秒
    timestamp_seconds = bigint_ts / 1000
    return datetime.datetime.fromtimestamp(timestamp_seconds)


def datetime_to_bigint(dt: datetime.datetime) -> int:
    """
    将 datetime 对象转换为 bigint 类型的时间戳（毫秒）
    :param dt: datetime 对象
    :return: 毫秒级时间戳
    """
    # 秒转毫秒
    timestamp_seconds = dt.timestamp()
    return int(timestamp_seconds * 1000)

def is_same_day(bigint_ts1: int, bigint_ts2: int) -> bool:
    """
    判断两个毫秒级时间戳是否属于同一天
    :param bigint_ts1: 毫秒级时间戳
    :param bigint_ts2: 毫秒级时间戳
    :return: 同一天返回 True，否则返回 False
    """
    dt1 = bigint_to_datetime(bigint_ts1)
    dt2 = bigint_to_datetime(bigint_ts2)
    return dt1.date() == dt2.date()

def within_hours(bigint_ts1: int, bigint_ts2: int, t: int) -> bool:
    """
    判断ts1相较于ts2相差是否不超过t小时
    :param bigint_ts1: 毫秒级时间戳
    :param bigint_ts2: 毫秒级时间戳
    :param t: 允许相差的小时数
    :return: 相差不超过t小时返回True，否则返回False
    """
    diff_ms = abs(bigint_ts1 - bigint_ts2)
    diff_hours = diff_ms / (1000 * 3600)
    return diff_hours <= t


def judge_platform_contain_relation(cur_platform, target_platform):
    """
    判断当前平台是否包含目标平台的关系
    :param cur_platform: 当前平台
    :param target_platform: 目标平台
    :return: 如果当前平台包含目标平台的关系，则返回True，否则返回False
    """
    target_platform = target_platform.strip().lower()
    if " " in target_platform:
        target_platform = target_platform.split(" ")
    elif "," in target_platform:
        target_platform = target_platform.split(",")
    if target_platform == 'all':
        return True
    if cur_platform.lower() in ['kuaishou', 'ks']:
        if 'ks' in target_platform or 'kuaishou' in target_platform:
            return True
        else:
            return False
    if cur_platform.lower() in ['weibo', 'wb']:
        if 'wb' in target_platform or 'weibo' in target_platform:
            return True
        else:
            return False
    if cur_platform.lower() in ['xiaohongshu', 'xhs']:
        if 'xhs' in target_platform or 'xiaohongshu' in target_platform:
            return True
        else:
            return False
    if cur_platform.lower() in ['zhihu', 'zh']:
        if 'zh' in target_platform or 'zhihu' in target_platform:
            return True
        else:
            return False
    if cur_platform.lower() in ['douyin', 'dy']:
        if 'dy' in target_platform or 'douyin' in target_platform:
            return True
        else:
            return False
        
def update_keyword_search_interval(last_interval: int) -> int:
    """
    更新关键词的搜索间隔时间。
    :param keyword_id: 关键词ID
    :param last_update_time: 上次更新时间（毫秒级时间戳）
    :param update_interval: 搜索间隔时间（小时）
    """
    if last_interval == 24:
        return 72
    elif last_interval == 72:
        return 168
    else:
        return 100000000
    