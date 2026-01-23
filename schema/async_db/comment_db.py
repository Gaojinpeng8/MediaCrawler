from typing import Optional, List, Any
from schema import CommentEntity, ExtractInfoEntity


class CommentDB:
    """`comment` 表的异步 CRUD 封装。"""

    def __init__(self, db: Any = None):
        # 允许直接传入 AsyncMysqlDB，或留空走 ContextVar 获取
        self._db = db

    def _get_db(self):
        if self._db is not None:
            # 兼容传入 ContextVar 或 AsyncMysqlDB 实例
            if hasattr(self._db, 'get'):
                return self._db.get()
            return self._db
        try:
            from var import media_crawler_mysqldb_var
        except ImportError:
            from media_crawler.var import media_crawler_mysqldb_var
        return media_crawler_mysqldb_var.get()

    async def get_by_id(self, id: int) -> Optional[CommentEntity]:
        """按主键获取一条评论记录。"""
        async_db_conn = self._get_db()
        sql = "SELECT * FROM comment WHERE id = %s"
        res = await async_db_conn.get_first(sql, id, map_to=CommentEntity)
        return res

    async def get_extract_info_by_comment_id(self, comment_id: int) -> Optional[ExtractInfoEntity]:
        """根据评论ID获取对应的AI分析结果。"""
        async_db_conn = self._get_db()
        sql = "SELECT * FROM extract_info WHERE content_id = %s AND content_type = 3"
        res = await async_db_conn.get_first(sql, comment_id, content_type=3, map_to=ExtractInfoEntity)
        return res

    async def get_extract_info_by_comment_ids(self, comment_ids: List[int]) -> List[ExtractInfoEntity]:
        """根据多个评论ID获取对应的AI分析结果。"""
        if not comment_ids:
            return []
        async_db_conn = self._get_db()
        placeholders = ','.join(['%s'] * len(comment_ids))
        sql = f"SELECT * FROM extract_info WHERE content_id IN ({placeholders}) AND content_type = 3"
        return await async_db_conn.query(sql, *comment_ids, map_to=ExtractInfoEntity)

    async def get_comments_by_plan_id(self, plan_id: int) -> List[CommentEntity]:
        """根据监控方案ID获取所有关联的评论。"""
        async_db_conn = self._get_db()
        sql = """
            SELECT cmt.* FROM comment cmt
            JOIN plan_content pc ON cmt.content_id = pc.content_id
            WHERE pc.plan_id = %s AND pc.content_type = 3
            ORDER BY cmt.comment_time DESC
        """
        return await async_db_conn.query(sql, plan_id, map_to=CommentEntity)

    async def get_comments_by_search_keyword_id(self, search_keyword_id: int, search_keyword: Optional[str] = None) -> List[CommentEntity]:
        """根据搜索关键词ID获取所有关联的评论。"""
        async_db_conn = self._get_db()
        if search_keyword:
            sql = """
                SELECT cmt.* FROM comment cmt
                JOIN plan_content pc ON cmt.content_id = pc.content_id
                WHERE pc.keyword_id LIKE %s AND pc.content_type = 3
                ORDER BY cmt.comment_time DESC
            """
            keyword_pattern = f"{search_keyword_id}-{search_keyword}%"
            return await async_db_conn.query(sql, keyword_pattern, map_to=CommentEntity)
        else:
            sql = """
                SELECT cmt.* FROM comment cmt
                JOIN plan_content pc ON cmt.content_id = pc.content_id
                WHERE pc.keyword_id LIKE %s AND pc.content_type = 3
                ORDER BY cmt.comment_time DESC
            """
            keyword_pattern = f"{search_keyword_id}-%"
            return await async_db_conn.query(sql, keyword_pattern, map_to=CommentEntity)