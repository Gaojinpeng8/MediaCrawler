from typing import Optional, List, Any

from schema import SearchKeywordsEntity


class SearchKeywordsDB:
    """`search_keywords` 表的异步 CRUD 封装。"""

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

    async def insert(self, item: SearchKeywordsEntity | dict) -> int:
        """插入一条关键词记录，返回新插入的主键ID。"""
        async_db_conn = self._get_db()
        return await async_db_conn.item_to_table('search_keywords', item)

    async def get_by_id(self, id: int) -> Optional[SearchKeywordsEntity]:
        """按主键获取一条记录。"""
        async_db_conn = self._get_db()
        sql = "SELECT * FROM search_keywords WHERE id = %s"
        res = await async_db_conn.get_first(sql, id, map_to=SearchKeywordsEntity)
        return res

    async def get_by_plan_id(self, plan_id: int) -> Optional[SearchKeywordsEntity]:
        """按方案ID获取最新一条记录。"""
        async_db_conn = self._get_db()
        sql = "SELECT * FROM search_keywords WHERE plan_id = %s ORDER BY create_time DESC LIMIT 1"
        res = await async_db_conn.get_first(sql, plan_id, map_to=SearchKeywordsEntity)
        return res

    async def list_by_plan_id(self, plan_id: int, limit: Optional[int] = None) -> List[SearchKeywordsEntity]:
        """按方案ID获取关键词列表，按创建时间倒序，可选限制条数。"""
        async_db_conn = self._get_db()
        if limit is not None:
            sql = "SELECT * FROM search_keywords WHERE plan_id = %s ORDER BY create_time DESC LIMIT %s"
            return await async_db_conn.query(sql, plan_id, limit, map_to=SearchKeywordsEntity)
        sql = "SELECT * FROM search_keywords WHERE plan_id = %s ORDER BY create_time DESC"
        return await async_db_conn.query(sql, plan_id, map_to=SearchKeywordsEntity)

    async def update_keywords(self, id: int, keywords: str) -> int:
        """更新指定记录的关键词内容。返回受影响行数。"""
        async_db_conn = self._get_db()
        return await async_db_conn.update_table('search_keywords', {'keywords': keywords}, {'id': id})
    
    async def update_last_update_time_and_interval(self, id: int, last_update_time: int, update_interval: int) -> int:
        """更新指定记录的最后更新时间和更新间隔。返回受影响行数。"""
        async_db_conn = self._get_db()
        
        return await async_db_conn.update_table('search_keywords', {'last_update_time': last_update_time, 'update_interval': update_interval}, {'id': id})

    async def delete_by_id(self, id: int) -> int:
        """删除指定主键的记录。返回受影响行数。"""
        async_db_conn = self._get_db()
        sql = "DELETE FROM search_keywords WHERE id = %s"
        return await async_db_conn.execute(sql, id)
    
    async def select_all(self) -> List[SearchKeywordsEntity]:
        """获取所有记录。"""
        async_db_conn = self._get_db()
        sql = "SELECT * FROM search_keywords"
        return await async_db_conn.query(sql, map_to=SearchKeywordsEntity)