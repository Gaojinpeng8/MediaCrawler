from typing import Optional, List, Any
from schema import ContentEntity, CommentEntity, ExtractInfoEntity


class ContentDB:
    """`content` 表的异步 CRUD 封装。"""

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

    async def get_by_id(self, id: int) -> Optional[ContentEntity]:
        """按主键获取一条内容记录。"""
        async_db_conn = self._get_db()
        sql = "SELECT * FROM content WHERE id = %s"
        res = await async_db_conn.get_first(sql, id, map_to=ContentEntity)
        return res

    async def get_by_content_id_and_source(self, content_id: str, content_source: str) -> Optional[ContentEntity]:
        """根据内容ID和来源平台获取内容记录。"""
        async_db_conn = self._get_db()
        sql = "SELECT * FROM content WHERE content_id = %s AND content_source = %s"
        res = await async_db_conn.get_first(sql, content_id, content_source, map_to=ContentEntity)
        return res

    async def get_comments_by_content_id(self, content_id: str) -> List[CommentEntity]:
        """根据帖子ID获取所有评论。"""
        async_db_conn = self._get_db()
        sql = "SELECT * FROM comment WHERE content_id = %s ORDER BY comment_time DESC"
        return await async_db_conn.query(sql, content_id, map_to=CommentEntity)

    async def get_extract_info_by_content_id(self, content_id: int, content_type: int = 2) -> Optional[ExtractInfoEntity]:
        """根据内容ID获取对应的AI分析结果。"""
        async_db_conn = self._get_db()
        sql = "SELECT * FROM extract_info WHERE content_id = %s AND content_type = %s"
        res = await async_db_conn.get_first(sql, content_id, content_type, map_to=ExtractInfoEntity)
        return res

    async def get_extract_info_by_content_ids(self, content_ids: List[int], content_type: int = 2) -> List[ExtractInfoEntity]:
        """根据多个内容ID获取对应的AI分析结果。"""
        if not content_ids:
            return []
        async_db_conn = self._get_db()
        placeholders = ','.join(['%s'] * len(content_ids))
        sql = f"SELECT * FROM extract_info WHERE content_id IN ({placeholders}) AND content_type = %s"
        return await async_db_conn.query(sql, *content_ids, content_type, map_to=ExtractInfoEntity)

    async def get_contents_by_keyword_id(self, keyword_id: str) -> List[ContentEntity]:
        """根据关键词ID获取关联的所有帖子。"""
        async_db_conn = self._get_db()
        sql = """
            SELECT c.* FROM content c
            JOIN plan_content pc ON c.id = pc.content_id
            WHERE pc.keyword_id LIKE %s AND pc.content_type = 2
            ORDER BY c.content_time DESC
        """
        return await async_db_conn.query(sql, f"%{keyword_id}%", map_to=ContentEntity)

    async def get_contents_by_plan_id(self, plan_id: int) -> List[ContentEntity]:
        """根据监控方案ID获取所有关联的帖子。"""
        async_db_conn = self._get_db()
        sql = """
            SELECT c.* FROM content c
            JOIN plan_content pc ON c.id = pc.content_id
            WHERE pc.plan_id = %s AND pc.content_type = 2
            ORDER BY c.content_time DESC
        """
        return await async_db_conn.query(sql, plan_id, map_to=ContentEntity)

    async def get_contents_by_search_keyword_id(self, search_keyword_id: int, search_keyword: Optional[str] = None) -> List[ContentEntity]:
        """根据搜索关键词ID获取所有关联的帖子。"""
        async_db_conn = self._get_db()
        if search_keyword:
            sql = """
                SELECT c.* FROM content c
                JOIN plan_content pc ON c.id = pc.content_id
                WHERE pc.keyword_id LIKE %s AND pc.content_type = 2
                ORDER BY c.content_time DESC
            """
            keyword_pattern = f"{search_keyword_id}-{search_keyword}%"
            return await async_db_conn.query(sql, keyword_pattern, map_to=ContentEntity)
        else:
            sql = """
                SELECT c.* FROM content c
                JOIN plan_content pc ON c.id = pc.content_id
                WHERE pc.keyword_id LIKE %s AND pc.content_type = 2
                ORDER BY c.content_time DESC
            """
            keyword_pattern = f"{search_keyword_id}-%"
            return await async_db_conn.query(sql, keyword_pattern, map_to=ContentEntity)