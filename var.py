# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/NanmiCoder/MediaCrawler/blob/main/var.py
# GitHub: https://github.com/NanmiCoder
# Licensed under NON-COMMERCIAL LEARNING LICENSE 1.1
#


# 声明：本代码仅供学习和研究目的使用。使用者应遵守以下原则：
# 1. 不得用于任何商业用途。
# 2. 使用时应遵守目标平台的使用条款和robots.txt规则。
# 3. 不得进行大规模爬取或对平台造成运营干扰。
# 4. 应合理控制请求频率，避免给目标平台带来不必要的负担。
# 5. 不得用于任何非法或不当的用途。
#
# 详细许可条款请参阅项目根目录下的LICENSE文件。
# 使用本代码即表示您同意遵守上述原则和LICENSE中的所有条款。

"""
MediaCrawler 上下文变量管理模块

该模块定义了项目中使用的所有上下文变量（ContextVar），用于在异步操作中共享状态。
上下文变量在不同的协程任务中保持独立，避免了全局变量的线程安全问题，
同时也减少了函数参数的传递层级，提高了代码的可维护性。

主要应用场景：
1. 爬虫任务中的关键词传递
2. 数据库连接池的共享
3. 评论爬取任务的管理
4. 爬虫类型的标识
"""

# 导入类型定义
from asyncio.tasks import Task
# 导入上下文变量库
from contextvars import ContextVar
# 导入类型提示
from typing import List

# 导入异步MySQL库
import aiomysql

from motor.motor_asyncio import AsyncIOMotorClient

from async_db import AsyncMongoDB, AsyncMysqlDB


# 请求关键词上下文变量 - 用于存储当前爬取任务的关键词
request_keyword_var: ContextVar[str] = ContextVar("request_keyword", default="")

# 爬虫类型上下文变量 - 用于标识当前爬虫的类型（如search、hot等）
crawler_type_var: ContextVar[str] = ContextVar("crawler_type", default="")

# 评论任务列表上下文变量 - 用于存储当前爬虫任务中创建的所有评论爬取子任务
comment_tasks_var: ContextVar[List[Task]] = ContextVar("comment_tasks", default=[])

# 数据库连接池上下文变量 - 用于在不同的数据库操作函数中共享同一个连接池
# 注意：该变量没有默认值，需要在程序初始化时设置
db_conn_pool_var: ContextVar[aiomysql.Pool] = ContextVar("db_conn_pool_var")

# 源关键词上下文变量 - 用于存储原始的搜索关键词
source_keyword_var: ContextVar[str] = ContextVar("source_keyword", default="")

# 社会心态新增
media_crawler_mongodb_var: ContextVar[AsyncMongoDB] = ContextVar("media_crawler_mongodb_var")
mongodb_conn_client_var: ContextVar[AsyncIOMotorClient] = ContextVar("mongodb_conn_client_var")
media_crawler_mysqldb_var: ContextVar[AsyncMysqlDB] = ContextVar[AsyncMysqlDB]("media_crawler_mysqldb_var")
mysqldb_conn_pool_var: ContextVar[aiomysql.Pool] = ContextVar("mysqldb_conn_pool_var")
db_conn_pool_var: ContextVar[aiomysql.Pool] = ContextVar("db_conn_pool_var")