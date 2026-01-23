# 声明：本代码仅供学习和研究目的使用。使用者应遵守以下原则：
# 1. 不得用于任何商业用途。
# 2. 使用时应遵守目标平台的使用条款和robots.txt规则。
# 3. 不得进行大规模爬取或对平台造成运营干扰。
# 4. 应合理控制请求频率，避免给目标平台带来不必要的负担。
# 5. 不得用于任何非法或不当的用途。
#
# 详细许可条款请参阅项目根目录下的LICENSE文件。
# 使用本代码即表示您同意遵守上述原则和LICENSE中的所有条款。

# -*- coding: utf-8 -*-
# @Author  : relakkes@gmail.com
# @Time    : 2024/1/14 18:46
# @Desc    :
from typing import List, Optional

import config
from var import source_keyword_var

from ._store_impl import *
from .douyin_store_media import *
from ._store_impl import *
from schema.async_db import PlanContentDB
from schema import PlanContentEntity


class DouyinStoreFactory:
    STORES = {
        "csv": DouyinCsvStoreImplement,
        "db": DouyinDbStoreImplement,
        "json": DouyinJsonStoreImplement,
        "sqlite": DouyinSqliteStoreImplement,
        "mongodb": DouyinMongoStoreImplement,
    }

    @staticmethod
    def create_store(cfg: Optional[object] = None) -> AbstractStore:
        """
        根据传入的配置对象选择存储实现；如未传入则回退到全局 config。
        说明：为支持多线程/多任务不同配置并行，优先使用参数 cfg。
        """
        save_opt = getattr(cfg, "SAVE_DATA_OPTION", None) if cfg is not None else None
        store_class = DouyinStoreFactory.STORES.get(save_opt or config.SAVE_DATA_OPTION)
        if not store_class:
            raise ValueError("[DouyinStoreFactory.create_store] Invalid save option only supported csv or db or json or sqlite or mongodb ...")
        return store_class()


def _extract_note_image_list(aweme_detail: Dict) -> List[str]:
    """
    提取笔记图片列表

    Args:
        aweme_detail (Dict): 抖音内容详情

    Returns:
        List[str]: 笔记图片列表
    """
    images_res: List[str] = []
    images: List[Dict] = aweme_detail.get("images", [])

    if not images:
        return []

    for image in images:
        image_url_list = image.get("url_list", [])  # download_url_list 为带水印的图片，url_list 为无水印的图片
        if image_url_list:
            images_res.append(image_url_list[-1])

    return images_res


def _extract_comment_image_list(comment_item: Dict) -> List[str]:
    """
    提取评论图片列表

    Args:
        comment_item (Dict): 抖音评论

    Returns:
        List[str]: 评论图片列表
    """
    images_res: List[str] = []
    image_list: List[Dict] = comment_item.get("image_list", [])

    if not image_list:
        return []

    for image in image_list:
        image_url_list = image.get("origin_url", {}).get("url_list", [])
        if image_url_list and len(image_url_list) > 1:
            images_res.append(image_url_list[1])

    return images_res


def _extract_content_cover_url(aweme_detail: Dict) -> str:
    """
    提取视频封面地址

    Args:
        aweme_detail (Dict): 抖音内容详情

    Returns:
        str: 视频封面地址
    """
    res_cover_url = ""

    video_item = aweme_detail.get("video", {})
    raw_cover_url_list = (video_item.get("raw_cover", {}) or video_item.get("origin_cover", {})).get("url_list", [])
    if raw_cover_url_list and len(raw_cover_url_list) > 1:
        res_cover_url = raw_cover_url_list[1]

    return res_cover_url


def _extract_video_download_url(aweme_detail: Dict) -> str:
    """
    提取视频下载地址

    Args:
        aweme_detail (Dict): 抖音视频

    Returns:
        str: 视频下载地址
    """
    video_item = aweme_detail.get("video", {})
    url_h264_list = video_item.get("play_addr_h264", {}).get("url_list", [])
    url_256_list = video_item.get("play_addr_256", {}).get("url_list", [])
    url_list = video_item.get("play_addr", {}).get("url_list", [])
    actual_url_list = url_h264_list or url_256_list or url_list
    if not actual_url_list or len(actual_url_list) < 2:
        return ""
    return actual_url_list[-1]


def _extract_music_download_url(aweme_detail: Dict) -> str:
    """
    提取音乐下载地址

    Args:
        aweme_detail (Dict): 抖音视频

    Returns:
        str: 音乐下载地址
    """
    music_item = aweme_detail.get("music", {})
    play_url = music_item.get("play_url", {})
    music_url = play_url.get("uri", "")
    return music_url


async def update_douyin_aweme(aweme_item: Dict, cfg: Optional[object] = None):
    aweme_id = aweme_item.get("aweme_id")
    user_info = aweme_item.get("author", {})
    interact_info = aweme_item.get("statistics", {})
    save_content_item = {
        "content_source": "dy",
        "content_id": aweme_id,
        "content_title": aweme_item.get("desc", ""),
        "content_desc": aweme_item.get("desc", ""),
        "content_time": aweme_item.get("create_time") or utils.get_current_timestamp(),
        "content_user_id": user_info.get("uid"),
        "content_user_home": f"https://www.douyin.com/user/{user_info.get('sec_uid')}",
        "content_user_nickname": user_info.get("nickname"),
        "content_user_gender": user_info.get("gender", -1),
        "content_liked_cnt": str(interact_info.get("digg_count", 0)),
        "content_collected_cnt": str(interact_info.get("collect_count", 0)),
        "content_comment_cnt": str(interact_info.get("comment_count", 0)),
        "content_shared_cnt": str(interact_info.get("share_count", 0)),
        "content_ip": aweme_item.get("ip_label", ""),
        "content_crawl_time": utils.get_current_timestamp(),
        "content_url": f"https://www.douyin.com/video/{aweme_id}",
        "content_cover_url": _extract_content_cover_url(aweme_item),
        "content_videos": _extract_video_download_url(aweme_item),
        "content_musics": _extract_music_download_url(aweme_item),
        "content_pics": ",".join(_extract_note_image_list(aweme_item))
    }
    dy_store = DouyinStoreFactory.create_store(cfg)
    utils.logger.info(f"[store.douyin.update_douyin_aweme] douyin aweme id:{aweme_id}, title:{save_content_item.get('content_title')}")
    content_id = await dy_store.store_content(content_item=save_content_item)
    if content_id:
        utils.logger.info(f"[store.douyin.update_douyin_aweme] douyin aweme id:{aweme_id}, content_id:{content_id}")
        extract_info_item = {
            "content_id": content_id,
            "content_type": "2",
            "content_source": 'dy',
            "domain": ""
        }
        dy_store.store_extract_info(extract_info_item)
        # 监控方案与内容关联：写入 plan_content 表
        try:
            plan_id = getattr(cfg, 'MONITOR_PLAN_ID', -1) if cfg is not None else -1
            keyword_id = getattr(cfg, 'SEARCH_KEYWORD_ID', -1) if cfg is not None else -1
            if plan_id != -1 and keyword_id != -1:
                plan_content_db = PlanContentDB()
                exist_item = await plan_content_db.query_by_plan_content(plan_id, content_id, content_type=2)
                if not exist_item:
                    plan_content_item = PlanContentEntity(
                        plan_id=plan_id,
                        content_id=content_id,
                        content_type=2,
                        keyword_id=keyword_id,
                    )
                    await plan_content_db.insert(plan_content_item)
        except Exception as e:
            utils.logger.error(f"[store.douyin.update_douyin_aweme] plan_content link failed: {e}")
    
    
    
    

async def batch_update_dy_aweme_comments(aweme_id: str, comments: List[Dict], cfg: Optional[object] = None):
    if not comments:
        return
    for comment_item in comments:
        await update_dy_aweme_comment(aweme_id, comment_item, cfg)


async def update_dy_aweme_comment(aweme_id: str, comment_item: Dict, cfg: Optional[object] = None):
    comment_aweme_id = comment_item.get("aweme_id")
    if aweme_id != comment_aweme_id:
        utils.logger.error(f"[store.douyin.update_dy_aweme_comment] comment_aweme_id: {comment_aweme_id} != aweme_id: {aweme_id}")
        return
    user_info = comment_item.get("user", {})
    comment_id = comment_item.get("cid")
    # 父评论ID：一级评论为 0，子评论为其父评论的 cid
    parent_comment_id_raw = comment_item.get("reply_id", "0") or "0"
    try:
        parent_comment_id = int(parent_comment_id_raw)
    except Exception:
        # 兜底转换，确保与表结构中的 int 类型一致
        parent_comment_id = 0
    save_comment_item = {
        "comment_id": comment_id,
        "comment_source": "dy",
        "comment_time": comment_item.get("create_time"),
        "comment_ip": comment_item.get("ip_label", ""),
        "content_id": aweme_id,
        "comment_desc": comment_item.get("text"),
        "comment_user_id": user_info.get("uid"),
        "comment_user_home": f"https://www.douyin.com/user/{user_info.get('sec_uid')}",
        "comment_user_nickname": user_info.get("nickname"),
        "sub_comment_cnt": str(comment_item.get("reply_comment_total", 0)),
        "comment_liked_cnt": (comment_item.get("digg_count") if comment_item.get("digg_count") else 0),
        "comment_crawl_time": utils.get_current_timestamp(),
        "par_comment_id": parent_comment_id,
        "comment_pics": json.dumps(_extract_comment_image_list(comment_item), ensure_ascii=False),
    }
    utils.logger.info(f"[store.douyin.update_dy_aweme_comment] douyin aweme comment: {comment_id}, content: {save_comment_item.get('comment_desc')}")
    dy_store = DouyinStoreFactory.create_store(cfg)
    comment_id = await dy_store.store_comment(comment_item=save_comment_item)
    if comment_id:
        dy_store.store_extract_info({
            "content_id": comment_id,
            "content_type": "3",
            "content_source": 'dy',
            "domain": ""
        })


async def save_creator(user_id: str, creator: Dict, cfg: Optional[object] = None):
    user_info = creator.get("user", {})
    gender_map = {0: "未知", 1: "男", 2: "女"}
    avatar_uri = user_info.get("avatar_300x300", {}).get("uri")
    local_db_item = {
        "user_id": user_id,
        "nickname": user_info.get("nickname"),
        "gender": gender_map.get(user_info.get("gender"), "未知"),
        "avatar": f"https://p3-pc.douyinpic.com/img/{avatar_uri}" + r"~c5_300x300.jpeg?from=2956013662",
        "desc": user_info.get("signature"),
        "ip_location": user_info.get("ip_location"),
        "follows": user_info.get("following_count", 0),
        "fans": user_info.get("max_follower_count", 0),
        "interaction": user_info.get("total_favorited", 0),
        "videos_count": user_info.get("aweme_count", 0),
        "last_modify_ts": utils.get_current_timestamp(),
    }
    utils.logger.info(f"[store.douyin.save_creator] creator:{local_db_item}")
    await DouyinStoreFactory.create_store(cfg).store_creator(local_db_item)


async def update_dy_aweme_image(aweme_id, pic_content, extension_file_name):
    """
    更新抖音笔记图片
    Args:
        aweme_id:
        pic_content:
        extension_file_name:

    Returns:

    """

    await DouYinImage().store_image({"aweme_id": aweme_id, "pic_content": pic_content, "extension_file_name": extension_file_name})


async def update_dy_aweme_video(aweme_id, video_content, extension_file_name):
    """
    更新抖音短视频
    Args:
        aweme_id:
        video_content:
        extension_file_name:

    Returns:

    """

    await DouYinVideo().store_video({"aweme_id": aweme_id, "video_content": video_content, "extension_file_name": extension_file_name})
