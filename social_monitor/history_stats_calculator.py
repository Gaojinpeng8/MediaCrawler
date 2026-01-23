import datetime
from typing import Optional, Dict, List
from schema import (
    MonitorPlanEntity, SearchKeywordsEntity, ContentEntity, 
    CommentEntity, ExtractInfoEntity, HistoryEntity
)
from schema.async_db import (
    MonitorPlanDB, SearchKeywordsDB, ContentDB, 
    CommentDB, ExtractInfoDB, HistoryDB
)
from social_monitor.utils import datetime_to_bigint


class HistoryStatsCalculator:
    """历史统计信息计算器：负责计算热度相关的统计指标。"""
    
    def __init__(self):
        self.monitor_plan_db = MonitorPlanDB()
        self.search_keywords_db = SearchKeywordsDB()
        self.content_db = ContentDB()
        self.comment_db = CommentDB()
        self.extract_info_db = ExtractInfoDB()
        self.history_db = HistoryDB()
    
    def _calculate_sentiment_stats(self, extract_infos: List[ExtractInfoEntity]) -> Dict[str, int]:
        """计算情感分析统计信息。"""
        positive = negative = neutral = 0
        
        for extract_info in extract_infos:
            if extract_info.three_emo == 'positive':
                positive += 1
            elif extract_info.three_emo == 'negative':
                negative += 1
            elif extract_info.three_emo == 'neutral':
                neutral += 1
        
        return {
            'positive': positive,
            'negative': negative,
            'neutral': neutral
        }
    
    def _find_hottest_item(self, items: List, like_field: str) -> Optional[str]:
        """找到点赞数最高的项目ID。"""
        if not items:
            return None
        
        hottest_item = max(items, key=lambda x: getattr(x, like_field, 0) or 0)
        return getattr(hottest_item, 'content_id', getattr(hottest_item, 'id', None))
    
    async def calculate_stats_by_monitor_plan(self, monitor_plan_id: int, search_time: Optional[int] = None) -> Optional[HistoryEntity]:
        """根据监控方案ID计算统计信息。"""
        # 获取监控方案
        monitor_plan = await self.monitor_plan_db.select_monitor_by_plan_id(monitor_plan_id)
        if not monitor_plan:
            return None
        
        # 获取该方案的所有关键词
        search_keywords = await self.search_keywords_db.list_by_plan_id(monitor_plan_id)
        if not search_keywords:
            return None
        
        # 使用最新的关键词进行统计
        latest_keyword = search_keywords[0]
        return await self.calculate_stats_by_search_keyword(latest_keyword, search_time)
    
    async def calculate_stats_by_search_keyword(self, search_keyword: SearchKeywordsEntity, search_time: Optional[int] = None) -> Optional[HistoryEntity]:
        """根据搜索关键词计算统计信息。"""
        if search_time is None:
            search_time = datetime_to_bigint(datetime.datetime.now())
        
        # 获取关键词对应的所有帖子
        contents = await self.content_db.get_contents_by_search_keyword_id(search_keyword.id)
        
        # 获取所有帖子的评论
        all_comments = []
        content_extract_infos = []
        
        for content in contents:
            comments = await self.comment_db.get_comments_by_content_id(content.content_id)
            all_comments.extend(comments)
            
            # 获取帖子的extract_info
            extract_info = await self.content_db.get_extract_info_by_content_id(content.id)
            if extract_info:
                content_extract_infos.append(extract_info)
        
        # 获取所有评论的extract_info
        comment_ids = [comment.id for comment in all_comments]
        comment_extract_infos = await self.comment_db.get_extract_info_by_comment_ids(comment_ids) if comment_ids else []
        
        # 计算统计信息
        total_posts = len(contents)
        total_comments = len(all_comments)
        
        # 计算浏览量和点赞量统计
        total_views = sum([c.content_viewd_cnt or 0 for c in contents])
        total_likes = sum([c.content_liked_cnt or 0 for c in contents])
        avg_views = total_views // total_posts if total_posts > 0 else 0
        avg_likes = total_likes // total_posts if total_posts > 0 else 0
        
        # 计算情感统计
        post_sentiment_stats = self._calculate_sentiment_stats(content_extract_infos)
        comment_sentiment_stats = self._calculate_sentiment_stats(comment_extract_infos)
        
        # 找到最热门的帖子和评论
        hottest_post_id = self._find_hottest_item(contents, 'content_liked_cnt')
        hottest_comment_id = self._find_hottest_item(all_comments, 'comment_liked_cnt')
        
        # 创建历史记录实体
        history_entity = HistoryEntity(
            search_keyword_id=search_keyword.id,
            search_keyword=search_keyword.keywords,
            total_posts=total_posts,
            total_views=total_views,
            total_likes=total_likes,
            avg_views=avg_views,
            avg_likes=avg_likes,
            positive_comments=comment_sentiment_stats['positive'],
            negative_comments=comment_sentiment_stats['negative'],
            neutral_comments=comment_sentiment_stats['neutral'],
            positive_posts=post_sentiment_stats['positive'],
            negative_posts=post_sentiment_stats['negative'],
            neutral_posts=post_sentiment_stats['neutral'],
            hottest_post_id=hottest_post_id,
            hottest_comment_id=hottest_comment_id,
            search_time=search_time,
            create_time=datetime_to_bigint(datetime.datetime.now())
        )
        
        return history_entity
    
    async def save_history_stats(self, history_entity: HistoryEntity) -> int:
        """保存历史统计信息到数据库。"""
        return await self.history_db.insert(history_entity)
    
    async def get_latest_stats_by_search_keyword_id(self, search_keyword_id: int) -> Optional[HistoryEntity]:
        """获取指定搜索关键词ID的最新统计信息。"""
        return await self.history_db.get_latest_by_search_keyword_id(search_keyword_id)
    
    async def get_stats_history_by_search_keyword_id(self, search_keyword_id: int, limit: int = 10) -> List[HistoryEntity]:
        """获取指定搜索关键词ID的历史统计信息列表。"""
        return await self.history_db.get_by_search_keyword_id(search_keyword_id, limit)