# -*- coding: utf-8 -*-
# @Author  : relakkes@gmail.com
# @Time    : 2024/1/14 21:34
# @Desc    :

import re
from typing import List


# from .zhihu_store_image import *
from .zhihu_store_impl import *
from schema.async_db import PlanContentDB
from schema import PlanContentEntity


class ZhihustoreFactory:
    STORES = {
        "csv": ZhihuCsvStoreImplement,
        "db": ZhihuDbStoreImplement,
        "json": ZhihuJsonStoreImplement,
    }

    @staticmethod
    def create_store(config) -> AbstractStore:
        store_class = ZhihustoreFactory.STORES.get(config.SAVE_DATA_OPTION)
        if not store_class:
            raise ValueError(
                "[ZhihuStoreFactory.create_store] Invalid save option only supported csv or db or json ...")
        return store_class()

async def update_zhihu_hotlist(hotlist_item: Dict, rank: int, config):
    detail_text = hotlist_item.get("target").get('metrics_area').get('text').split(" ")
    hot_score = int(detail_text[0]) * 10000
    card_id = hotlist_item.get('card_id').split('_')
    zhF = ZhihustoreFactory.create_store(config)
    if hotlist_item.get("target").get('image_area').get('url') != "":
        pic_ids = await zhF.store_pic({"pic_urls": hotlist_item.get("target").get('image_area').get('url')})
    else:
        pic_ids = None
    save_hotlist_item = {
        "hot_title": hotlist_item.get("target").get('title_area').get('text'),
        "hot_time": utils.get_current_timestamp(),
        "hot_rank": rank,
        "hot_score": hot_score,
        "hot_source": "zh",
        "hot_question_id": card_id[1],
        "hot_desc": hotlist_item.get("target").get('excerpt_area').get('text'),
        "hot_question_answer_cnt": hotlist_item.get('feed_specific').get('answer_count'),
        "hot_question_url": hotlist_item.get("target").get('link').get('url'),
        "hot_pic_url": pic_ids
    }
    # utils.logger.info(f"[store.zhihu.update_zhihu_hotlist] zhihu hotlist: {save_hotlist_item}")
    content_id = await zhF.store_hotlist(save_hotlist_item)
    extract_info_item = {
        "content_id": content_id,
        "content_type": 1,
        "content_source": "zh",
        "domain": ""
    }
    await zhF.store_extract_info(extract_info_item)

async def update_zhihu_answer(answer_item: Dict, hot_id: None, config):
    pic_urls = []
    for thumbnail in answer_item.get("target").get("thumbnail_info").get("thumbnails"):
        pic_urls.append(thumbnail.get("url"))
    url_token = answer_item.get("target").get("author").get("url_token")
    clean_text = re.sub(r"<.*?>", "", answer_item.get("target").get("content"))
    zhF = ZhihustoreFactory.create_store(config)
    if pic_urls:
        pic_ids = await zhF.store_pic({"pic_urls": pic_urls})
    else:
        pic_ids = None
    question_id = answer_item["target"]["question"]["id"]
    answer_id = answer_item["target"]["id"]
    save_content_item = {
        "hot_id": hot_id,
        "content_source": "zh",
        "content_id": answer_id,
        "question_id": question_id,
        "content_crawl_time": utils.get_current_timestamp(),
        "content_desc": clean_text,
        "content_time": answer_item.get("target").get("created_time") * 1000,
        "content_user_id": answer_item.get("target").get("author").get("id"),
        "content_user_gender": answer_item.get("target").get("author").get("gender"),
        "content_user_nickname": answer_item.get("target").get("author").get("name"),
        "content_user_home": f"https://www.zhihu.com/people/{url_token}",
        "content_liked_cnt": answer_item.get("target").get("voteup_count"),
        "content_comment_cnt": answer_item.get("target").get("comment_count", 0),
        "content_url": f"https://www.zhihu.com/question/{question_id}/answer/{answer_id}",
        "content_pics": pic_ids,
    }
    config.ZH_ANSWER_ID_LIST.append(save_content_item.get('content_id'))
    # utils.logger.info(
        # f"[store.zhihu.update_zhihu_answer] zhihu answer id:{save_content_item.get('content_id')}, excerpt: {save_content_item.get('content_desc')[:24]} ...")
    content_id = await zhF.store_content(save_content_item)
    extract_info_item = {
        "content_id": content_id,
        "content_type": 2,
        "content_source": "zh",
        "domain": ""
    }
    await zhF.store_extract_info(extract_info_item)
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
        utils.logger.error(f"[store.zhihu.update_zhihu_answer] plan_content link failed: {e}")

def extract_text_from_html(html: str) -> str:
    """Extract text from HTML, removing all tags."""
    if not html:
        return ""

    # Remove script and style elements
    clean_html = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', html, flags=re.DOTALL)
    # Remove all other tags
    clean_text = re.sub(r'<[^>]+>', '', clean_html).strip()
    return clean_text

async def update_zhihu_search_note(note_item: Dict, config):
    # pic_urls = []
    # for thumbnail in note_item.get("thumbnail_info").get("thumbnails"):
    #     pic_urls.append(thumbnail.get("url"))
    zhF = ZhihustoreFactory.create_store(config)
    # if pic_urls:
    #     pic_ids = await zhF.store_pic({"pic_urls": pic_urls})
    # else:
    pic_ids = None
    note_item = dict(note_item)
    question_id = note_item.get("question")
    answer_id = note_item["content_id"]
    content_user_nickname = note_item.get("user_nickname")
    save_content_item = {
        "content_source": "zh",
        "content_id": answer_id,
        "question_id": question_id,
        "content_crawl_time": utils.get_current_timestamp(),
        "content_title": extract_text_from_html(note_item.get("title")),
        "content_desc": extract_text_from_html(note_item.get("content_text", ""))[:512],
        "content_time": note_item.get("created_time"),
        "content_user_id": note_item.get("user_id'"),
        "content_user_gender": note_item.get("gender", '1'),
        "content_user_nickname": content_user_nickname,
        "content_user_home": f"https://www.zhihu.com/people/{content_user_nickname}",
        "content_liked_cnt": note_item.get("voteup_count", 0),
        "content_comment_cnt": note_item.get("comment_count", 0),
        "content_url": f"https://www.zhihu.com/question/{question_id}/answer/{answer_id}" if question_id else f"https://zhuanlan.zhihu.com/p/{answer_id}",
        "content_pics": pic_ids,
    }
    # config.ZH_ANSWER_ID_LIST.append(save_content_item.get('content_id'))
    # utils.logger.info(
        # f"[store.zhihu.update_zhihu_answer] zhihu answer id:{save_content_item.get('content_id')}, excerpt: {save_content_item.get('content_desc')[:24]} ...")
    content_id = await zhF.store_content(save_content_item)
    extract_info_item = {
        "content_id": content_id,
        "content_type": 2,
        "content_source": "zh",
        "domain": ""
    }
    await zhF.store_extract_info(extract_info_item)
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
        utils.logger.error(f"[store.zhihu.update_zhihu_search_note] plan_content link failed: {e}")

async def batch_update_zhihu_note_comments(note_id: str, comments: List[Dict], note_type: str, config):
    if not comments:
        return
    for comment_item in comments:
        await update_zhihu_note_comment(note_id, comment_item, note_type, config)

async def update_zhihu_note_comment(note_id: str, comment_item: Dict, note_type: str, config):
    if note_type == "questions":
        content_id = f'{note_id}'
    else:
        content_id = f'{note_id}'
    # if len(comment_item['comment_tag']) > 0:
    #     user_ip = comment_item["comment_tag"][0]['text']
    # else:
    user_ip = comment_item['ip_location']
    url_token = ""
    comment_desc = comment_item['content']
    clean_text = re.sub(r"<.*?>", "", comment_desc)
    save_comment_item = {
        "content_id": content_id,
        "comment_id": comment_item['comment_id'],
        "par_comment_id": comment_item['parent_comment_id'],
        "comment_crawl_time": utils.get_current_timestamp(),
        "comment_time": comment_item['publish_time'] * 1000,
        "comment_desc": clean_text,
        "sub_comment_cnt": comment_item['sub_comment_count'],
        "comment_liked_cnt": comment_item['like_count'],
        "comment_ip": user_ip,
        "comment_user_id": comment_item['user_id'],
        "comment_user_nickname": comment_item['user_nickname'],
        "comment_user_gender": comment_item.get('gender', '1'),
        "comment_user_home": f"https://www.zhihu.com/people/{url_token}",
        "comment_source": "zh"  
    }
    # utils.logger.info(
        # f"[store.zhihu.update_zhihu_note_comment] zhihu note comment: {save_comment_item['comment_id']}, content: {save_comment_item.get('content', '')[:24]} ...")
    zhF = ZhihustoreFactory.create_store(config)
    content_id = await zhF.store_comment(save_comment_item)
    extract_info_item = {
        "content_id": content_id,
        "content_type": 3,
        "content_source": "zh",
        "domain": ""
    }
    await zhF.store_extract_info(extract_info_item)