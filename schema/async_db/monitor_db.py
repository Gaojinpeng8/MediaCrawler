from var import media_crawler_mysqldb_var
from typing import Optional, List
from db import AsyncMysqlDB
from schema import MonitorPlanEntity

class MonitorPlanDB:
    def __init__(self, db: AsyncMysqlDB = media_crawler_mysqldb_var):
        self.db = db
        
    async def select_monitor_by_plan_id(self, plan_id: int) -> Optional[MonitorPlanEntity]:
        # 使用 SQLAlchemy ORM 模型构建查询
        
        async_db_conn: AsyncMysqlDB = self.db.get()
        sql: str  = f"select * from monitor_plan where plan_id = %s"
        result = await async_db_conn.query(sql, plan_id, map_to=MonitorPlanEntity)
        return result[0]
    
    async def select_monitors(self,) -> List[MonitorPlanEntity]:
        # 使用 SQLAlchemy ORM 模型构建查询
        
        async_db_conn: AsyncMysqlDB = self.db.get()
        sql: str  = f"select * from monitor_plan order by create_time desc"
        result = await async_db_conn.query(sql, map_to=MonitorPlanEntity)
        return result
    async def select_init_monitor(self) -> List[MonitorPlanEntity]:
        # 使用 SQLAlchemy ORM 模型构建查询
        
        async_db_conn: AsyncMysqlDB = self.db.get()
        # sql: str  = f"SELECT * FROM monitor_plan WHERE last_update_tim e IS NOT NULL AND ABS(last_update_time - create_time) <= 10000;"
        sql: str  = f"SELECT * FROM monitor_plan ORDER BY create_time DESC;"
        result = await async_db_conn.query(sql, map_to=MonitorPlanEntity)
        return result
    
    async def select_monitors_by_status(self, status: int) -> List[MonitorPlanEntity]:
        # 使用 SQLAlchemy ORM 模型构建查询
        
        async_db_conn: AsyncMysqlDB = self.db.get()
        sql: str  = f"select * from monitor_plan where status = %s"
        result = await async_db_conn.query(sql, status, map_to=MonitorPlanEntity)
        return result
    
    async def update_last_update_time(self, monitor_id: int, last_update_time: int) -> None:
        # 使用 SQLAlchemy ORM 模型构建查询
        
        async_db_conn: AsyncMysqlDB = self.db.get()
        sql: str  = f"update monitor_plan set last_update_time = %s where plan_id = %s"
        await async_db_conn.execute(sql, last_update_time, monitor_id)
    
