# -*- coding: utf-8 -*-
# @Author  : relakkes@gmail.com
# @Time    : 2024/4/6 14:54
# @Desc    : mediacrawler 数据库管理模块
"""
mediacrawler 数据库管理模块

该模块负责管理媒体爬虫的数据库连接，包括：
1. MySQL 数据库连接的初始化与关闭
2. MongoDB 数据库连接的初始化与关闭
3. 数据库连接池的管理
4. 历史数据的修复

支持异步操作，使用 aiomysql 和 motor 库实现异步数据库访问
"""

import asyncio
from typing import Dict
from urllib.parse import urlparse

# 导入异步文件操作库
import aiofiles
# 导入异步 MySQL 库
import aiomysql
# 导入异步 MongoDB 客户端
from motor.motor_asyncio import AsyncIOMotorClient

# 导入配置文件
import config
# 导入自定义数据库类
from async_db import AsyncMongoDB, AsyncMysqlDB
# 导入工具函数
from tools import utils
# 导入上下文变量，用于存储数据库连接对象
from var import (
    media_crawler_mongodb_var,     # MongoDB 操作对象
    mongodb_conn_client_var,       # MongoDB 客户端连接
    media_crawler_mysqldb_var,     # MySQL 操作对象
    mysqldb_conn_pool_var          # MySQL 连接池
)


def parse_mysql_url(mysql_url) -> Dict:
    """
    解析 MySQL 连接 URL
    
    由于 aiomysql 不支持直接以 URL 方式传递连接信息，需要将 URL 解析为字典格式
    
    参数:
        mysql_url: str - MySQL 连接 URL，格式如: mysql://root:password@localhost:3306/media_crawler
    
    返回:
        Dict - 解析后的数据库连接参数字典
        包含: host, port, user, password, db
    """
    # 解析 URL
    parsed_url = urlparse(mysql_url)
    
    # 构建数据库连接参数字典
    db_params = {
        'host': parsed_url.hostname,           # 数据库主机名
        'port': parsed_url.port or 3306,       # 数据库端口，默认3306
        'user': parsed_url.username,           # 数据库用户名
        'password': parsed_url.password,       # 数据库密码
        'db': parsed_url.path.lstrip('/')      # 数据库名称，移除路径开头的'/'
    }
    
    return db_params


async def init_mediacrawler_db():
    """
    初始化媒体爬虫数据库连接
    
    功能流程：
    1. 解析MySQL连接URL，获取连接参数
    2. 创建MySQL连接池
    3. 初始化MySQL操作对象并存储到上下文变量
    4. 创建MongoDB客户端连接
    5. 初始化MongoDB操作对象并存储到上下文变量
    
    使用上下文变量存储数据库连接对象，方便在其他模块中访问
    """
    # 解析MySQL连接URL，获取连接参数
    db_conn_params = parse_mysql_url(config.RELATION_DB_URL)
    
    # 创建MySQL连接池
    pool = await aiomysql.create_pool(
        autocommit=True,  # 自动提交事务
        **db_conn_params  # 传递数据库连接参数
    )
    
    # 初始化MySQL操作对象
    async_db_obj = AsyncMysqlDB(pool)
    
    # 将连接池和MySQL操作对象存储到上下文变量
    mysqldb_conn_pool_var.set(pool)
    media_crawler_mysqldb_var.set(async_db_obj)
    
    # 创建MongoDB客户端连接
    client = AsyncIOMotorClient(config.MG_DB_URL)
    
    # 初始化MongoDB操作对象
    async_db_obj = AsyncMongoDB(client)
    
    # 将MongoDB客户端和操作对象存储到上下文变量
    mongodb_conn_client_var.set(client)
    media_crawler_mongodb_var.set(async_db_obj)

async def fix_extract_info_domain_nulls():
    """
    修复历史数据中的 NULL 值
    
    将 extract_info 表中 domain 字段为 NULL 的记录更新为空字符串
    此操作是幂等的，多次执行不会产生副作用
    
    执行时机：在 MySQL 连接初始化完成后执行
    异常处理：不阻断主流程，仅记录异常日志
    """
    try:
        # 从上下文变量获取MySQL操作对象
        async_db_obj: AsyncMysqlDB = media_crawler_mysqldb_var.get()
        
        # 如果MySQL操作对象不存在，直接返回
        if async_db_obj is None:
            return
        
        # 执行SQL更新语句，将NULL值替换为空字符串
        await async_db_obj.execute("UPDATE extract_info SET domain = '' WHERE domain IS NULL")
    except Exception as e:
        # 不阻断主流程，仅记录异常日志
        utils.logger.error(f"[init_db] 修复 extract_info.domain NULL 失败: {e}")
async def init_db():
    """
    初始化数据库连接（主入口函数）
    
    功能流程：
    1. 获取日志记录器
    2. 记录数据库初始化开始日志
    3. 调用init_mediacrawler_db初始化MySQL和MongoDB连接
    4. 修复历史数据中的NULL值
    5. 记录数据库初始化结束日志
    
    这是数据库初始化的主入口函数，被外部模块调用
    """
    # 获取日志记录器
    logger = utils.get_logger(config.PLATFORM)
    
    # 记录数据库初始化开始日志
    logger.info("数据库连接初始化开始")
    
    # 初始化MySQL和MongoDB连接
    await init_mediacrawler_db()
    
    # 修复历史脏数据，避免实体映射校验报错
    await fix_extract_info_domain_nulls()
    
    # 记录数据库初始化结束日志
    logger.info("数据库连接初始化结束")

async def close():
    """
    关闭数据库连接
    
    功能流程：
    1. 获取日志记录器
    2. 关闭MySQL连接池
    3. 关闭MongoDB客户端连接
    4. 记录数据库连接关闭日志
    
    异常处理：
    - 关闭MySQL连接池时忽略异常，确保退出流程不中断
    - 关闭MongoDB客户端时不捕获异常（由上层处理）
    """
    # 获取日志记录器
    logger = utils.get_logger(config.PLATFORM)
    
    # 关闭MySQL连接池
    db_pool: aiomysql.Pool = mysqldb_conn_pool_var.get()
    if db_pool is not None:
        # 先关闭连接池
        db_pool.close()
        try:
            # 等待所有连接关闭，避免事件循环销毁时触发析构异常
            await db_pool.wait_closed()
        except Exception:
            # 忽略关闭阶段的异常，确保退出流程不中断
            pass
    
    # 关闭MongoDB客户端连接
    client: AsyncIOMotorClient = mongodb_conn_client_var.get()
    if client is not None:
        client.close()
    
    # 记录数据库连接关闭日志
    logger.info("数据库连接关闭")

if __name__ == '__main__':
    """
    程序入口（直接运行时）
    
    当直接运行db.py文件时，执行数据库初始化操作
    用于测试数据库连接功能
    """
    # 获取事件循环并运行数据库初始化函数
    asyncio.get_event_loop().run_until_complete(init_db())
