import argparse
import logging
from loguru import logger
import os
import sys
from typing import Dict

from .crawler_util import *
from .slider_util import *
from .time_util import *


# def init_loging_config():
#     level = logging.INFO
#     logging.basicConfig(
#         level=level,
#         format="%(asctime)s [%(threadName)s] %(name)s %(levelname)s (%(filename)s:%(lineno)d) - %(message)s",
#         datefmt='%Y-%m-%d %H:%M:%S'
#     )
#     _logger = logging.getLogger("MediaCrawler")
#     _logger.setLevel(level)
#     return _logger


# logger = init_loging_config()


# cookie/base.py

def cookie_dict_to_str(cookie_dict: dict[str, str]) -> str:
    """
    Convert cookie dict to HTTP Cookie header string
    - 自动过滤空值
    - 自动转 str
    """
    return "; ".join(
        f"{k}={v}"
        for k, v in cookie_dict.items()
        if k and v is not None and v != ""
    )

class CookieFilter:
    WHITELIST: set[str] = set()
    MAX_VALUE_LEN = 600
    MAX_TOTAL_LEN = 1500

    @classmethod
    def filter(cls, raw_cookie: Dict[str, str]) -> Dict[str, str]:
        filtered = {
            k: v for k, v in raw_cookie.items()
            if k in cls.WHITELIST and len(v) < cls.MAX_VALUE_LEN
        }

        # 兜底：总长度限制（防 431）
        total_len = sum(len(k) + len(v) for k, v in filtered.items())
        if total_len > cls.MAX_TOTAL_LEN:
            # 按 value 长度从小到大保留
            items = sorted(filtered.items(), key=lambda x: len(x[1]))
            trimmed = {}
            size = 0
            for k, v in items:
                size += len(k) + len(v)
                if size > cls.MAX_TOTAL_LEN:
                    break
                trimmed[k] = v
            return trimmed

        return filtered

class KuaishouCookieFilter(CookieFilter):
    WHITELIST = {
        "did",
        "clientid",
        "kpf",
        "userId",
        "kuaishou.server.webday7_st",
        "kuaishou.server.webday7_ph",
    }

class DouyinCookieFilter(CookieFilter):
    WHITELIST = {
        "ttwid",
        "odin_tt",
        "sid_tt",
        "passport_csrf_token",
        "msToken",
    }

class ZhihuCookieFilter(CookieFilter):
    WHITELIST = {
        "_zap",
        "d_c0",
        "z_c0",
        "__zse_ck",
    }

class WeiboCookieFilter(CookieFilter):
    WHITELIST = {
        "SUB",
        "SUBP",
        "SSOLoginState",
        "ALF",
    }


FILTER_MAP = {
    'ks': KuaishouCookieFilter,
    'douyin': DouyinCookieFilter,
    'zh': ZhihuCookieFilter,
    'weibo': WeiboCookieFilter,
}

def route_cookie(
    platform: str,
    raw_cookie: Dict[str, str],
) -> Dict[str, str]:
    if platform not in FILTER_MAP:
        raise ValueError(f"Unsupported platform: {platform}")
    return FILTER_MAP[platform].filter(raw_cookie)



def get_logger(plaform: str):
    folder_ = "./log/"
    prefix_ = f"{plaform}/"
    rotation_ = "10 MB"
    retention_ = "5 days"
    encoding_ = "utf-8"
    backtrace_ = True
    diagnose_ = True

    # 格式里面添加了process和thread记录，方便查看多进程和线程程序
    format_ = '<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> ' \
                '| <magenta>{process}</magenta>:<yellow>{thread}</yellow> ' \
                '| <cyan>{name}</cyan>:<cyan>{function}</cyan>:<yellow>{line}</yellow> - <level>{message}</level>'

    # 确保日志目录存在
    os.makedirs(os.path.join(folder_, prefix_), exist_ok=True)

    logger.remove()
    # 控制台输出：满足“也输出到控制台”的需求
    logger.add(sys.stdout, level="INFO", backtrace=backtrace_, diagnose=diagnose_,
               format=format_, colorize=True, enqueue=True)
    # 这里面采用了层次式的日志记录方式，就是低级日志文件会记录比他高的所有级别日志，这样可以做到低等级日志最丰富，高级别日志更少更关键
    # info
    logger.add(folder_ + prefix_ + "info.log", level="INFO", backtrace=backtrace_, diagnose=diagnose_,
                format=format_, colorize=False, enqueue=True,
                rotation=rotation_, retention=retention_, encoding=encoding_,
                filter=lambda record: record["level"].no >= logger.level("INFO").no)

    # error
    logger.add(folder_ + prefix_ + "error.log", level="ERROR", backtrace=backtrace_, diagnose=diagnose_,
                format=format_, colorize=False, enqueue=True,
                rotation=rotation_, retention=retention_, encoding=encoding_,
                filter=lambda record: record["level"].no >= logger.level("ERROR").no)
    return logger


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


def dict2object(config_dict: Dict):
    import types
    config = types.SimpleNamespace(**config_dict)
    return config
    
def module2object(config):
    custom_attributes = [attr for attr in dir(config) if not attr.startswith('__') and not attr.endswith('__')][:-3]
    new_config = {}
    for attr in custom_attributes:
        new_config[attr] = getattr(config, attr)
    return dict2object(new_config)
