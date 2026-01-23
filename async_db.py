# -*- coding: utf-8 -*-
# @Author  : 
# @Time    : 2024/7/14 14:21
# @Desc    : 异步AsyncIOMotorClient的增删改查封装
from typing import Any, Dict, List, Union, Optional, Type

from motor.motor_asyncio import AsyncIOMotorClient
import aiomysql
import config
class AsyncMongoDB: 
    def __init__(self, client: AsyncIOMotorClient) -> None:
        self.client = client

    async def insert(self, collection_name: str, item: Dict):
        db = self.client[config.MG_DB_DATABASE]
        col = db[collection_name]
        res = await col.insert_one(item)
        return str(res.inserted_id)

    async def query(self, collection_name: str, myquery: Optional[Dict] = None, myprojection: Optional[Dict] = None, mysort: Optional[Dict] = None, mylimit: int = None) -> List[Dict]:
        if myquery is None:
            myquery = {}
        if myprojection is None:
            myprojection = {} 
        db = self.client[config.MG_DB_DATABASE]
        col = db[collection_name]
        res = []
        async for document in col.find(myquery, myprojection, limit=mylimit, sort=mysort):
            res.append(document)
        return res
    
class AsyncMysqlDB:
    def __init__(self, pool: aiomysql.Pool) -> None:
        self.__pool = pool

    async def query(self, sql: str, *args: Union[str, int], map_to: Optional[Type] = None) -> List[Union[Dict[str, Any], Any]]:
        """
        从给定的 SQL 中查询记录，返回的是一个列表
        :param sql: 查询的sql
        :param args: sql中传递动态参数列表
        :return:
        """
        async with self.__pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(sql, args)
                data = await cur.fetchall()
                if not data:
                    return []
                if map_to is None:
                    return data
                # 将字典记录映射为指定的 Pydantic/实体类实例
                res = []
                for row in data:
                    if hasattr(map_to, 'model_validate'):
                        # Pydantic v2
                        res.append(map_to.model_validate(row))
                    else:
                        # 普通数据类或自定义类
                        res.append(map_to(**row))
                return res

    async def get_first(self, sql: str, *args: Union[str, int], map_to: Optional[Type] = None) -> Union[Dict[str, Any], Any, None]:
        """
        从给定的 SQL 中查询记录，返回的是符合条件的第一个结果
        :param sql: 查询的sql
        :param args:sql中传递动态参数列表
        :return:
        """
        async with self.__pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(sql, args)
                data = await cur.fetchone()
                if data is None:
                    return None
                if map_to is None:
                    return data
                if hasattr(map_to, 'model_validate'):
                    return map_to.model_validate(data)
                return map_to(**data)

    async def item_to_table(self, table_name: str, item: Union[Dict[str, Any], Any]) -> int:
        """
        表中插入数据
        :param table_name: 表名
        :param item: 一条记录的字典信息
        :return:
        """
        # 支持传入 Pydantic 模型或一般对象
        if hasattr(item, 'model_dump'):
            data = item.model_dump(exclude_none=True)
        elif isinstance(item, dict):
            data = {k: v for k, v in item.items() if v is not None}
        else:
            # 兜底：尝试使用 __dict__
            data = {k: v for k, v in getattr(item, '__dict__', {}).items() if v is not None}

        fields = list(data.keys())
        values = list(data.values())
        fields = [f'`{field}`' for field in fields]
        fieldstr = ','.join(fields)
        # 占位符数量必须与过滤后的 values 数量一致
        valstr = ','.join(['%s'] * len(values))
        sql = "INSERT INTO %s (%s) VALUES(%s)" % (table_name, fieldstr, valstr)
        async with self.__pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(sql, values)
                lastrowid = cur.lastrowid
                return lastrowid

    async def update_table(self, table_name: str, updates: Union[Dict[str, Any], Any], 
                           where_conditions: Dict[str, Union[str, int, float]]) -> int:
        """
        更新指定表的记录
        :param table_name: 表名
        :param updates: 需要更新的字段和值的 key - value 映射
        :param where_conditions: where 条件中的字段键值对列表
        :return:
        """
        upsets = []
        values = []
        # 支持传入 Pydantic 模型或一般对象
        if hasattr(updates, 'model_dump'):
            upd = updates.model_dump(exclude_none=True)
        elif isinstance(updates, dict):
            upd = {k: v for k, v in updates.items() if v is not None}
        else:
            upd = {k: v for k, v in getattr(updates, '__dict__', {}).items() if v is not None}

        for k, v in upd.items():
            s = '`%s`=%%s' % k
            upsets.append(s)
            values.append(v)
        upsets = ','.join(upsets)

        where_clauses = []
        for field, value in where_conditions.items():
            where_clauses.append(f'{field}=%s')
            values.append(value)
        where_clause = ' AND '.join(where_clauses)

        sql = f"UPDATE {table_name} SET {upsets} WHERE {where_clause}"
        async with self.__pool.acquire() as conn:
            async with conn.cursor() as cur:
                rows = await cur.execute(sql, values)
                return rows

    async def execute(self, sql: str, *args: Union[str, int]) -> int:
        """
        需要更新、写入等操作的 excute 执行语句
        :param sql:
        :param args:
        :return:
        """
        async with self.__pool.acquire() as conn:
            async with conn.cursor() as cur:
                rows = await cur.execute(sql, args)
                return rows