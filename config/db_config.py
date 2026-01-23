# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/NanmiCoder/MediaCrawler/blob/main/config/db_config.py
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


import os

# mysql config
MYSQL_DB_PWD = os.getenv("MYSQL_DB_PWD", "cqu1701")
MYSQL_DB_USER = os.getenv("MYSQL_DB_USER", "root")
MYSQL_DB_HOST = os.getenv("MYSQL_DB_HOST", "10.242.14.65")
MYSQL_DB_PORT = os.getenv("MYSQL_DB_PORT", 3306)
MYSQL_DB_NAME = os.getenv("MYSQL_DB_NAME", "social_monitor_dev")

# 统一使用 URL 供 db.py 解析
RELATION_DB_URL = f"mysql://{MYSQL_DB_USER}:{MYSQL_DB_PWD}@{MYSQL_DB_HOST}:{MYSQL_DB_PORT}/{MYSQL_DB_NAME}"


mysql_db_config = {
    "user": MYSQL_DB_USER,
    "password": MYSQL_DB_PWD,
    "host": MYSQL_DB_HOST,
    "port": MYSQL_DB_PORT,
    "db_name": MYSQL_DB_NAME,
}


# redis config
REDIS_DB_HOST = os.getenv("REDIS_DB_HOST", "127.0.0.1")  # your redis host
REDIS_DB_PWD = os.getenv("REDIS_DB_PWD", "123456")  # your redis password
REDIS_DB_PORT = os.getenv("REDIS_DB_PORT", 6379)  # your redis port
REDIS_DB_NUM = os.getenv("REDIS_DB_NUM", 0)  # your redis db num

# cache type
CACHE_TYPE_REDIS = "redis"
CACHE_TYPE_MEMORY = "memory"

# sqlite config
SQLITE_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "sqlite_tables.db")

sqlite_db_config = {
    "db_path": SQLITE_DB_PATH
}

# mongodb config
MONGODB_HOST = os.getenv("MONGODB_HOST", "localhost")
MONGODB_PORT = os.getenv("MONGODB_PORT", 27017)
MONGODB_USER = os.getenv("MONGODB_USER", "")
MONGODB_PWD = os.getenv("MONGODB_PWD", "")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "media_crawler")

mongodb_config = {
    "host": MONGODB_HOST,
    "port": int(MONGODB_PORT),
    "user": MONGODB_USER,
    "password": MONGODB_PWD,
    "db_name": MONGODB_DB_NAME,
}

# postgres config
POSTGRES_DB_PWD = os.getenv("POSTGRES_DB_PWD", "123456")
POSTGRES_DB_USER = os.getenv("POSTGRES_DB_USER", "postgres")
POSTGRES_DB_HOST = os.getenv("POSTGRES_DB_HOST", "localhost")
POSTGRES_DB_PORT = os.getenv("POSTGRES_DB_PORT", 5432)
POSTGRES_DB_NAME = os.getenv("POSTGRES_DB_NAME", "media_crawler")

postgres_db_config = {
    "user": POSTGRES_DB_USER,
    "password": POSTGRES_DB_PWD,
    "host": POSTGRES_DB_HOST,
    "port": POSTGRES_DB_PORT,
    "db_name": POSTGRES_DB_NAME,
}

# mongodb config
MG_DB_HOST = os.getenv("MG_DB_HOST", "10.242.14.65")
MG_DB_PWD = os.getenv("MG_DB_PWD", "cqu1701")
MG_DB_PORT = os.getenv("MG_DB_PORT", 27017)
MG_DB_USER = os.getenv("MG_DB_USER", "social_monitor_dev")
MG_DB_DATABASE = os.getenv("MG_DB_DATABASE", "admin")

MG_DB_URL = f"mongodb://{MG_DB_USER}:{MG_DB_PWD}@{MG_DB_HOST}:{MG_DB_PORT}"

# 兼容旧代码路径：保留旧命名的字典（若有旧模块使用）
mongodb_config = {
    "host": MG_DB_HOST,
    "port": int(MG_DB_PORT),
    "user": MG_DB_USER,
    "password": MG_DB_PWD,
    "db_name": MG_DB_DATABASE,
}

# 向后兼容旧 mongodb 变量命名
MONGODB_HOST = MG_DB_HOST
MONGODB_PORT = MG_DB_PORT
MONGODB_USER = MG_DB_USER
MONGODB_PWD = MG_DB_PWD
MONGODB_DB_NAME = MG_DB_DATABASE