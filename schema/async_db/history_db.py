from typing import Optional, List, Any
from schema import HistoryEntity


class HistoryDB:
    """`history` 表的异步 CRUD 封装。"""

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

    async def insert(self, item: HistoryEntity | dict) -> int:
        """插入一条历史记录，返回新插入的主键ID。"""
        async_db_conn = self._get_db()
        return await async_db_conn.item_to_table('history', item)

    async def get_by_id(self, id: int) -> Optional[HistoryEntity]:
        """按主键获取一条记录。"""
        async_db_conn = self._get_db()
        sql = "SELECT * FROM history WHERE id = %s"
        res = await async_db_conn.get_first(sql, id, map_to=HistoryEntity)
        return res

    async def get_by_search_keyword_id(self, search_keyword_id: int, limit: Optional[int] = None) -> List[HistoryEntity]:
        """按搜索关键词ID获取历史记录列表，按搜索时间倒序。"""
        async_db_conn = self._get_db()
        if limit is not None:
            sql = "SELECT * FROM history WHERE search_keyword_id = %s ORDER BY search_time DESC LIMIT %s"
            return await async_db_conn.query(sql, search_keyword_id, limit, map_to=HistoryEntity)
        sql = "SELECT * FROM history WHERE search_keyword_id = %s ORDER BY search_time DESC"
        return await async_db_conn.query(sql, search_keyword_id, map_to=HistoryEntity)

    async def get_by_keyword_and_keyword_id(self, search_keyword_id: int, search_keyword: str, limit: Optional[int] = None) -> List[HistoryEntity]:
        """按搜索关键词ID和具体关键词获取历史记录列表，按搜索时间倒序。"""
        async_db_conn = self._get_db()
        if limit is not None:
            sql = "SELECT * FROM history WHERE search_keyword_id = %s AND search_keyword = %s ORDER BY search_time DESC LIMIT %s"
            return await async_db_conn.query(sql, search_keyword_id, search_keyword, limit, map_to=HistoryEntity)
        sql = "SELECT * FROM history WHERE search_keyword_id = %s AND search_keyword = %s ORDER BY search_time DESC"
        return await async_db_conn.query(sql, search_keyword_id, search_keyword, map_to=HistoryEntity)

    async def update_by_id(self, id: int, data: dict) -> int:
        """根据ID更新记录，返回受影响行数。"""
        async_db_conn = self._get_db()
        return await async_db_conn.update_table('history', data, {'id': id})

    async def delete_by_id(self, id: int) -> int:
        """删除指定主键的记录。返回受影响行数。"""
        async_db_conn = self._get_db()
        sql = "DELETE FROM history WHERE id = %s"
        return await async_db_conn.execute(sql, id)

    async def get_latest_by_search_keyword_id(self, search_keyword_id: int) -> Optional[HistoryEntity]:
        """获取指定搜索关键词ID的最新一条历史记录。"""
        async_db_conn = self._get_db()
        sql = "SELECT * FROM history WHERE search_keyword_id = %s ORDER BY search_time DESC LIMIT 1"
        res = await async_db_conn.get_first(sql, search_keyword_id, map_to=HistoryEntity)
        return res