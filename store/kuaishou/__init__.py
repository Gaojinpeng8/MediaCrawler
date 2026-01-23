# -*- coding: utf-8 -*-
# @Author  : relakkes@gmail.com
# @Time    : 2024/1/14 20:03
# @Desc    :
from typing import List


from .kuaishou_store_impl import *
from schema.async_db import PlanContentDB
from schema import PlanContentEntity


class KuaishouStoreFactory:
    STORES = {
        "csv": KuaishouCsvStoreImplement,
        "db": KuaishouDbStoreImplement,
        "json": KuaishouJsonStoreImplement
    }

    @staticmethod
    def create_store(config) -> AbstractStore:
        store_class = KuaishouStoreFactory.STORES.get(config.SAVE_DATA_OPTION)
        if not store_class:
            raise ValueError(
                "[KuaishouStoreFactory.create_store] Invalid save option only supported csv or db or json ...")
        return store_class()

async def update_ks_hotlist(hotlist_item: Dict, config):
    save_hotlist_item = {
        "hot_title": hotlist_item.get("hot_title"),
        "hot_time": utils.get_current_timestamp(), 
        "hot_rank": hotlist_item.get("hot_rank"),
        "hot_score": int(float(hotlist_item.get("hot_score")[:-1]) * 10000),
        "hot_source": "ks",    
        "hot_video_ids": str(hotlist_item.get("hot_videoIds"))[1:-1]
    }
    # utils.logger.info(f"[store.xhs.update_xhs_hotlist] ks hotlist: {hotlist_item}")
    ksF = KuaishouStoreFactory.create_store(config)
    content_id = await ksF.store_hotlist(save_hotlist_item)
    extract_info_item = {
        "content_id": content_id,
        "content_type": 1,
        "content_source": "ks",
        "domain": ""
    }
    await ksF.store_extract_info(extract_info_item)

async def update_kuaishou_video(video_item: Dict, hot_id: None=None, config=None):
    photo_info: Dict = video_item.get("photo", {})
    if not photo_info:
        return 
    video_id = photo_info.get("id")
    if not video_id:
        return
    user_info = video_item.get("author", {})
    # 先存视频链接到mongoDB
    ksF = KuaishouStoreFactory.create_store(config)
    view_count = photo_info.get("viewCount")
    if view_count.endswith("万") or view_count.endswith("w") or view_count.endswith("W"):
        view_count = int(float(view_count[:-1]) * 10000)
    else:
        view_count = int(float(view_count))
    # content_download_id = await ksF.store_video({"video_download_url": photo_info.get("photoUrl", "")})
    save_content_item = {
        "hot_id": hot_id,
        "content_source": "ks",
        "content_title": photo_info.get("caption", ""),
        "content_desc": photo_info.get("caption", ""),
        "content_id": video_id,
        "content_crawl_time": utils.get_current_timestamp(),
        "content_time": photo_info.get("timestamp"),
        "content_user_id": user_info.get("id"),
        "content_user_home": f"https://www.kuaishou.com/profile/{user_info.get('id')}",
        "content_user_nickname": user_info.get("name"),
        "content_user_gender": user_info.get("gender", -1),
        "content_viewd_cnt": view_count,
        "content_liked_cnt": photo_info.get("realLikeCount"),
        "content_url": f"https://www.kuaishou.com/short-video/{video_id}",
        "content_cover_url": photo_info.get("coverUrl", ""),
        "content_videos": photo_info.get("photoUrl", ""),
    }
    # utils.logger.info(
        # f"[store.kuaishou.update_kuaishou_video] Kuaishou video id:{video_id}, title:{save_content_item.get('content_desc')[:50]}")
    content_id = await ksF.store_content(save_content_item)
    extract_info_item = {
        "content_id": content_id,
        "content_type": 2,
        "content_source": "ks",
        "domain": ""
    }
    await ksF.store_extract_info(extract_info_item)
    # 监控方案与内容关联：写入 plan_content 表
    try:
        if getattr(config, 'MONITOR_PLAN_ID', -1) != -1 and getattr(config, 'SEARCH_KEYWORD_ID', -1) != -1:
            plan_content_db = PlanContentDB()
            exist_item = await plan_content_db.query_by_plan_content(config.MONITOR_PLAN_ID, content_id, content_type=2)
            if not exist_item:
                plan_content_item = PlanContentEntity(
                    plan_id=config.MONITOR_PLAN_ID,
                    content_id=content_id,
                    content_type=2,
                    keyword_id=config.SEARCH_KEYWORD_ID,
                )
                await plan_content_db.insert(plan_content_item)
    except Exception as e:
        utils.logger.error(f"[store.kuaishou.update_kuaishou_video] plan_content link failed: {e}")

async def batch_update_ks_video_comments(video_id: str, comments: List[Dict], config):
    if not comments:
        return
    # utils.logger.info(f"[store.kuaishou.batch_update_ks_video_comments] video_id:{video_id}, comments:{comments}")
    for comment_item in comments:
        await update_ks_video_comment(video_id, comment_item, config)

async def update_ks_video_comment(video_id: str, comment_item: Dict, config):
    comment_id = comment_item.get("comment_id")
    if comment_item.get("commentCount", 0) == None:
        subCommentCount = 0
    else:
        subCommentCount = comment_item.get("commentCount", 0)
    save_comment_item = {
        "content_id": video_id,
        "comment_id": comment_id,
        "par_comment_id": comment_item.get("reply_to", "0"),
        "comment_crawl_time": utils.get_current_timestamp(),
        "comment_time": comment_item.get("timestamp"),
        "comment_desc": comment_item.get("content"),
        "sub_comment_cnt": subCommentCount,
        "comment_liked_cnt": comment_item.get("likedCount"),
        "comment_user_id": comment_item.get("author_id"),
        "comment_user_nickname": comment_item.get("author_name"),
        "comment_source": "ks"
    }
    # utils.logger.info(
        # f"[store.kuaishou.update_ks_video_comment] Kuaishou video comment: {comment_id}, content: {comment_item.get('comment_desc')}")
    ksF = KuaishouStoreFactory.create_store(config)
    content_id = await ksF.store_comment(save_comment_item)
    extract_info_item = {
        "content_id": content_id,
        "content_type": 3,
        "content_source": "ks",
        "domain": ""
    }
    await ksF.store_extract_info(extract_info_item)
