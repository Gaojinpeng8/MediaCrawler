from var import media_crawler_mysqldb_var
from typing import Optional, List
from db import AsyncMysqlDB
from schema import PlanContentEntity

class PlanContentDB:
    def __init__(self, db: AsyncMysqlDB = media_crawler_mysqldb_var):
        self.db = db
        
    async def query_by_plan_content(self, plan_id, content_id, content_type=2) -> Optional[PlanContentEntity]:
        # 使用 SQLAlchemy ORM 模型构建查询
        
        async_db_conn: AsyncMysqlDB = self.db.get()
        sql: str  = f"select * from plan_content where plan_id = %s and content_id = %s and content_type = %s"
        result = await async_db_conn.query(sql, plan_id, content_id, content_type, map_to=PlanContentEntity)
        return result[0] if result else None
    
    
    async def insert(self, plan_content_item: PlanContentEntity):
        async_db_conn: AsyncMysqlDB = self.db.get()
        sql: str = f"insert into plan_content (plan_id, content_id, content_type, keyword_id) values (%s, %s, %s, %s)"
        return await async_db_conn.execute(sql, plan_content_item.plan_id, plan_content_item.content_id, plan_content_item.content_type, plan_content_item.keyword_id)
    
