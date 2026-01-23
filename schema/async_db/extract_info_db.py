from typing import Optional, List, Any
from schema import ExtractInfoEntity


class ExtractInfoDB:
    """`extract_info` 表的异步 CRUD 封装。"""

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

    async def get_by_id(self, id: int) -> Optional[ExtractInfoEntity]:
        """按主键获取一条分析记录。"""
        async_db_conn = self._get_db()
        sql = "SELECT * FROM extract_info WHERE id = %s"
        res = await async_db_conn.get_first(sql, id, map_to=ExtractInfoEntity)
        return res

    async def get_by_content_id_and_type(self, content_id: int, content_type: int) -> Optional[ExtractInfoEntity]:
        """根据内容ID和类型获取分析结果。"""
        async_db_conn = self._get_db()
        sql = "SELECT * FROM extract_info WHERE content_id = %s AND content_type = %s"
        res = await async_db_conn.get_first(sql, content_id, content_type, map_to=ExtractInfoEntity)
        return res

    async def get_extract_infos_by_content_ids(self, content_ids: List[int], content_type: int) -> List[ExtractInfoEntity]:
        """根据多个内容ID获取对应的分析结果。"""
        if not content_ids:
            return []
        async_db_conn = self._get_db()
        placeholders = ','.join(['%s'] * len(content_ids))
        sql = f"SELECT * FROM extract_info WHERE content_id IN ({placeholders}) AND content_type = %s"
        return await async_db_conn.query(sql, *content_ids, content_type, map_to=ExtractInfoEntity)

    async def get_extract_infos_by_plan_id(self, plan_id: int, content_type: Optional[int] = None) -> List[ExtractInfoEntity]:
        """根据监控方案ID获取所有关联的分析结果。"""
        async_db_conn = self._get_db()
        if content_type is not None:
            sql = """
                SELECT ei.* FROM extract_info ei
                JOIN plan_content pc ON ei.content_id = pc.content_id
                WHERE pc.plan_id = %s AND pc.content_type = %s AND ei.content_type = %s
            """
            return await async_db_conn.query(sql, plan_id, content_type, content_type, map_to=ExtractInfoEntity)
        else:
            sql = """
                SELECT ei.* FROM extract_info ei
                JOIN plan_content pc ON ei.content_id = pc.content_id
                WHERE pc.plan_id = %s
            """
            return await async_db_conn.query(sql, plan_id, map_to=ExtractInfoEntity)

    async def get_extract_infos_by_search_keyword_id(self, search_keyword_id: int, search_keyword: Optional[str] = None, content_type: Optional[int] = None) -> List[ExtractInfoEntity]:
        """根据搜索关键词ID获取所有关联的分析结果。"""
        async_db_conn = self._get_db()
        
        base_sql = """
            SELECT ei.* FROM extract_info ei
            JOIN plan_content pc ON ei.content_id = pc.content_id
            WHERE pc.keyword_id LIKE %s
        """
        
        if search_keyword:
            keyword_pattern = f"{search_keyword_id}-{search_keyword}%"
        else:
            keyword_pattern = f"{search_keyword_id}-%"
        
        conditions = [keyword_pattern]
        
        if content_type is not None:
            base_sql += " AND pc.content_type = %s AND ei.content_type = %s"
            conditions.extend([content_type, content_type])
        
        base_sql += " ORDER BY ei.content_id"
        
        return await async_db_conn.query(base_sql, *conditions, map_to=ExtractInfoEntity)