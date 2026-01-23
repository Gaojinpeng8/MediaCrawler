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
# @Author  : persist1@126.com
# @Time    : 2025/9/5 19:34
# @Desc    : 抖音存储实现类
import asyncio
import json
import os
import pathlib
from typing import Dict, List

import aiofiles
from async_db import AsyncMysqlDB
from base.base_crawler import AbstractStore
from var import media_crawler_mysqldb_var
from tools import utils
from .douyin_store_sql import (
    add_new_content,
    add_new_comment,
    add_new_extract_info,
    update_content_by_content_id,
    update_comment_by_comment_id,
    update_extract_info,
    query_content_entity_by_content_id,
    query_comment_entity_by_comment_id,
    query_extract_info_entity,
)
# from database.db_session import get_session
# from database.models import DouyinAweme, DouyinAwemeComment, DyCreator
# from database.mongodb_store_base import MongoDBStoreBase



class DouyinCsvStoreImplement(AbstractStore):
    def __init__(self):
        self.file_writer = AsyncFileWriter(
            crawler_type=crawler_type_var.get(),
            platform="douyin"
        )

    async def store_content(self, content_item: Dict):
        """
        Douyin content CSV storage implementation
        Args:
            content_item: note item dict

        Returns:

        """
        await self.file_writer.write_to_csv(
            item=content_item,
            item_type="contents"
        )

    async def store_comment(self, comment_item: Dict):
        """
        Douyin comment CSV storage implementation
        Args:
            comment_item: comment item dict

        Returns:

        """
        await self.file_writer.write_to_csv(
            item=comment_item,
            item_type="comments"
        )

    async def store_creator(self, creator: Dict):
        """
        Douyin creator CSV storage implementation
        Args:
            creator: creator item dict

        Returns:

        """
        await self.file_writer.write_to_csv(
            item=creator,
            item_type="creators"
        )


class DouyinDbStoreImplement(AbstractStore):
    def __init__(self):
        self.async_db: AsyncMysqlDB = media_crawler_mysqldb_var.get()

    async def store_content(self, content_item: Dict):
        """
        抖音内容入库（统一入库到通用 content 表）
        Args:
            content_item: 来自 store/douyin/__init__.py 的 save_content_item
        """
        content_id = content_item.get("content_id") or content_item.get("aweme_id")
        if not content_id:
            return
        # 先查是否存在
        exist_row = await query_content_entity_by_content_id(content_id)
        # 清理 None，避免 SQL 更新报错
        clean_item = {k: v for k, v in content_item.items() if v is not None}
        if not exist_row:
            clean_item["content_crawl_time"] = utils.get_current_timestamp()
            return await add_new_content(clean_item)
        else:
            await update_content_by_content_id(content_id, clean_item)
            return exist_row.id
        
    async def store_comment(self, comment_item: Dict):
        """
        抖音评论入库（统一入库到通用 comment 表）
        Args:
            comment_item: 来自 store/douyin/__init__.py 的 save_comment_item
        """
        comment_id = comment_item.get("comment_id") or comment_item.get("cid")
        if not comment_id:
            return None
        # 清理 None

        exist_row = await query_comment_entity_by_comment_id(comment_id)
        if not exist_row:
            comment_item["comment_crawl_time"] = utils.get_current_timestamp()
            return await add_new_comment(comment_item)
        else:
            await update_comment_by_comment_id(comment_id, comment_item)
            return exist_row.id

    async def store_creator(self, creator: Dict):
        """
        Douyin creator DB storage implementation
        Args:
            creator: creator dict
        """
        user_id = creator.get("user_id")
        if not user_id:
            return
        exist_row = await self.async_db.get_first(
            "SELECT * FROM dy_creator WHERE user_id = %s",
            user_id
        )
        clean_item = {k: v for k, v in creator.items() if v is not None}
        if not exist_row:
            clean_item["add_ts"] = utils.get_current_timestamp()
            await self.async_db.item_to_table("dy_creator", clean_item)
        else:
            await self.async_db.update_table("dy_creator", clean_item, {"user_id": user_id})

    async def store_hotlist(self, hotlist_item: Dict):
        """抖音热榜入库（通用 hotlist 表）"""
        hot_title = hotlist_item.get("hot_title")
        clean_item = {k: v for k, v in hotlist_item.items() if v is not None}
        if hot_title:
            exist_row = await self.async_db.get_first(
                "SELECT * FROM hotlist WHERE hot_title = %s",
                hot_title
            )
            if not exist_row:
                return await self.async_db.item_to_table("hotlist", clean_item)
            else:
                await self.async_db.update_table("hotlist", clean_item, {"hot_title": hot_title})
                return exist_row.get("id") if isinstance(exist_row, dict) else None
        # 无标题时直接插入
        return await self.async_db.item_to_table("hotlist", clean_item)

    async def store_extract_info(self, extract_info_item: Dict):
        """AI 提取信息入库（通用 extract_info 表）"""
        content_id = extract_info_item.get("content_id")
        content_type = extract_info_item.get("content_type")
        content_source = extract_info_item.get("content_source")
        if content_id is None or content_type is None or content_source is None:
            # 关键字段缺失则忽略
            return
        exist_row = await query_extract_info_entity(content_id, content_type, content_source)
        clean_item = {k: v for k, v in extract_info_item.items() if v is not None}
        if not exist_row:
            return await add_new_extract_info(clean_item)
        else:
            await update_extract_info(content_id, content_type, content_source, clean_item)
            return exist_row.id if hasattr(exist_row, 'id') else None

    async def store_pic(self, pic_item):
        """图片URL直接以 JSON 字符串形式返回，供 content.content_pics 写入"""
        pic_urls = (pic_item or {}).get("pic_urls")
        if not pic_urls:
            return None
        try:
            return json.dumps(pic_urls, ensure_ascii=False)
        except Exception:
            return ",".join([str(u) for u in pic_urls])

    async def store_video(self, video_item):
        """视频链接占位实现：直接返回下载 URL 或 None"""
        if not video_item:
            return None
        return video_item.get("video_download_url")


class DouyinJsonStoreImplement(AbstractStore):
    def __init__(self):
        self.output_dir = os.path.join(os.getcwd(), "output", "douyin")
        os.makedirs(self.output_dir, exist_ok=True)

    async def store_content(self, content_item: Dict):
        """
        content JSON storage implementation
        Args:
            content_item:

        Returns:

        """
        await self._write_jsonl("contents", content_item)

    async def store_comment(self, comment_item: Dict):
        """
        comment JSON storage implementation
        Args:
            comment_item:

        Returns:

        """
        await self._write_jsonl("comments", comment_item)
        # 生成词云（与其他平台保持一致的开关语义）
        try:
            import config
            from tools.words import AsyncWordCloudGenerator
            from tools import utils
            import pathlib
            if getattr(config, "ENABLE_GET_WORDCLOUD", False) and getattr(config, "ENABLE_GET_COMMENTS", True):
                jsonl_path = os.path.join(self.output_dir, "comments.jsonl")
                if os.path.exists(jsonl_path) and os.path.getsize(jsonl_path) > 0:
                    # 读取 JSONL，提取 content 字段
                    filtered_data = []
                    async with aiofiles.open(jsonl_path, "r", encoding="utf-8") as f:
                        async for line in f:
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                item = json.loads(line)
                                content_text = item.get("content") or item.get("text") or ""
                                if content_text:
                                    filtered_data.append({"content": content_text})
                            except Exception:
                                continue

                    if filtered_data:
                        words_base_path = os.path.join("data", "douyin", "words")
                        pathlib.Path(words_base_path).mkdir(parents=True, exist_ok=True)
                        words_file_prefix = f"{words_base_path}/comments_{utils.get_current_date()}"
                        generator = AsyncWordCloudGenerator()
                        await generator.generate_word_frequency_and_cloud(filtered_data, words_file_prefix)
        except Exception:
            # 安静失败，不影响主流程
            pass

    async def store_creator(self, creator: Dict):
        """
        creator JSON storage implementation
        Args:
            creator:

        Returns:

        """
        await self._write_jsonl("creators", creator)

    async def store_hotlist(self, hotlist_item: Dict):
        """hotlist JSON storage implementation"""
        await self._write_jsonl("hotlist", hotlist_item)

    async def store_extract_info(self, extract_info_item: Dict):
        """extract_info JSON storage implementation"""
        await self._write_jsonl("extract_info", extract_info_item)

    async def store_pic(self, pic_item):
        """图片存储（JSON模式下不进行二进制存储，作为占位实现）"""
        return

    async def store_video(self, video_item):
        """视频存储（JSON模式下不进行二进制存储，作为占位实现）"""
        return

    async def _write_jsonl(self, item_type: str, item: Dict):
        file_path = os.path.join(self.output_dir, f"{item_type}.jsonl")
        async with aiofiles.open(file_path, "a", encoding="utf-8") as f:
            await f.write(json.dumps(item, ensure_ascii=False) + "\n")



class DouyinSqliteStoreImplement(DouyinDbStoreImplement):
    pass


class DouyinMongoStoreImplement(AbstractStore):
    """抖音MongoDB存储实现"""
    
    def __init__(self):
        self.mongo_store = MongoDBStoreBase(collection_prefix="douyin")

    async def store_content(self, content_item: Dict):
        """
        存储视频内容到MongoDB
        Args:
            content_item: 视频内容数据
        """
        aweme_id = content_item.get("aweme_id")
        if not aweme_id:
            return
        
        await self.mongo_store.save_or_update(
            collection_suffix="contents",
            query={"aweme_id": aweme_id},
            data=content_item
        )
        utils.logger.info(f"[DouyinMongoStoreImplement.store_content] Saved aweme {aweme_id} to MongoDB")

    async def store_comment(self, comment_item: Dict):
        """
        存储评论到MongoDB
        Args:
            comment_item: 评论数据
        """
        comment_id = comment_item.get("comment_id")
        if not comment_id:
            return
        
        await self.mongo_store.save_or_update(
            collection_suffix="comments",
            query={"comment_id": comment_id},
            data=comment_item
        )
        utils.logger.info(f"[DouyinMongoStoreImplement.store_comment] Saved comment {comment_id} to MongoDB")

    async def store_creator(self, creator_item: Dict):
        """
        存储创作者信息到MongoDB
        Args:
            creator_item: 创作者数据
        """
        user_id = creator_item.get("user_id")
        if not user_id:
            return
        
        await self.mongo_store.save_or_update(
            collection_suffix="creators",
            query={"user_id": user_id},
            data=creator_item
        )
        utils.logger.info(f"[DouyinMongoStoreImplement.store_creator] Saved creator {user_id} to MongoDB")
