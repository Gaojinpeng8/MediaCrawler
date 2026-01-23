#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
社交媒体监控爬虫主程序

该程序用于监控社交媒体平台上的热点事件和关键词，通过爬虫获取相关内容
支持的平台：知乎(zh)、抖音(douyin)、快手(ks)、微博(wb)
主要功能：
1. 初始化监控方案，获取热点事件关键词
2. 定期更新监控方案
3. 更新搜索关键词
4. 跨平台爬取相关内容和评论

作者: 未知
创建日期: 未知
版本: 未知
"""

import sys
import asyncio
import datetime
from tqdm import tqdm

# 添加当前目录到系统路径，确保模块导入正常
sys.path.append("./")

# 导入核心模块
from social_monitor.main_crawler import MainCrawler
import cmd_arg
import config

# 导入数据库相关模块
from schema.async_db import MonitorPlanDB, SearchKeywordsDB
from schema import SearchKeywordsEntity, MonitorPlanEntity

# 导入搜索工具
from social_monitor.mcp_client import KIMISearch, BAIDUSearch

# 导入工具函数
from social_monitor.utils import (
    datetime_to_bigint,      # 日期时间转换为大数
    within_hours,            # 判断时间是否在指定小时数内
    judge_platform_contain_relation,  # 判断平台包含关系
    update_keyword_search_interval     # 更新关键词搜索间隔
)

# 导入进度缓存
from social_monitor.src.progress_cache import KeywordProgressCache

async def get_keywords(monitor_plans: list[MonitorPlanEntity], time_range="最近三个月的", nums=10, monitor_time_interval=24, check_node=None) -> dict:
    """
    获取监控方案对应的关键词
    
    支持两种模式：
    1. create模式：获取刚刚插入的初始化关键词
    2. update模式：正常更新获取关键词
    
    参数:
        monitor_plans: list[MonitorPlanEntity] - 监控方案列表
        time_range: str - 搜索时间范围，默认为"最近三个月的"
        nums: int - 获取关键词数量，默认为10
        monitor_time_interval: int - 监控时间间隔（小时），默认为24
        check_node: str - 检查节点，可选值为'create'或'update'
    
    返回:
        dict - 监控方案ID与对应关键词的映射字典
        格式: {monitor_plan_id: [keyword1, keyword2, ..., search_keyword_id]}
    """
    # 验证check_node参数
    if check_node is None or check_node not in ['create', 'update']:
        return {}
    
    # 初始化数据库连接和搜索工具
    search_keywords_db = SearchKeywordsDB()
    search_tools = [KIMISearch(), BAIDUSearch()]  # 使用KIMI和百度搜索工具
    search_task_list = {}  # 存储监控方案ID与关键词的映射
    
    # 遍历所有监控方案，显示详细进度
    with tqdm(monitor_plans, desc="处理监控方案", unit="方案") as pbar:
        for monitor_plan in pbar:
            # 在进度条描述中显示当前方案名称
            pbar.set_description(f"处理方案: {monitor_plan.plan_name[:20]}...")
            
            # 获取该方案已有的关键词记录
            search_keywords_entity = await search_keywords_db.get_by_plan_id(monitor_plan.plan_id)
            
            # 若已存在关键词记录且仍在时间间隔内，则直接复用
            if search_keywords_entity:
                # 根据check_node选择不同的检查时间
                check_time = (
                    search_keywords_entity.create_time if check_node == 'create'
                    else search_keywords_entity.last_update_time
                )
                
                # 检查是否在监控时间间隔内
                current_time = datetime_to_bigint(datetime.datetime.now())
                # 是否需要检查
                check_flag = True
                if check_flag or within_hours(check_time, current_time, monitor_time_interval):
                    # 复用现有关键词，格式：[关键词列表, search_keyword_id]
                    search_task_list[monitor_plan.plan_id] = (
                        search_keywords_entity.keywords.split(config.KEYWORD_SEPARATOR) + 
                        [search_keywords_entity.id]
                    )
                    continue
            
            # 若没有现有关键词或已过期，则重新搜索
            for search_tool in search_tools:
                # 使用搜索工具获取关键词
                keywords = search_tool.search_init_monitor(monitor_plan, time_range, nums)
                
                # 初始化该方案的关键词列表
                if search_task_list.get(monitor_plan.plan_id) is None:
                    search_task_list[monitor_plan.plan_id] = []
                
                # 添加非空关键词
                search_task_list[monitor_plan.plan_id].extend(
                    [word for word in keywords if len(word.strip()) > 0]
                )
            
            # 若没有获取到任何关键词，则跳过
            if len(search_task_list[monitor_plan.plan_id]) == 0:
                continue
            
            # 将关键词保存到数据库
            search_keyword_id = await search_keywords_db.insert(SearchKeywordsEntity(
                create_time=datetime_to_bigint(datetime.datetime.now()),
                plan_id=monitor_plan.plan_id,
                keywords=config.KEYWORD_SEPARATOR.join(search_task_list[monitor_plan.plan_id])
            ))
            
            # 将search_keyword_id添加到关键词列表末尾
            search_task_list[monitor_plan.plan_id].append(search_keyword_id)
    
    return search_task_list
    
async def init_monitor_plan(config_obj, num_keywords=15, max_crawler_notes_count=15):
    """
    初始化监控方案，获取社会热点事件并爬取相关内容
    
    功能流程：
    1. 获取需要初始化的监控方案
    2. 为每个方案获取热点关键词
    3. 初始化爬虫并登录各平台
    4. 对每个关键词在各平台进行搜索和爬取
    5. 更新关键词和监控方案的最后更新时间
    
    参数:
        config_obj: 配置对象，包含爬虫的基本配置
        num_keywords: int - 每个监控方案获取的关键词数量，默认为15
        max_crawler_notes_count: int - 每个关键词爬取的最大内容数量，默认为15
    """
    print("======获取社会热点事件========")
    
    # 初始化数据库连接
    monitor_plan_db = MonitorPlanDB()
    
    # 获取需要初始化的监控方案
    monitor_plans = await monitor_plan_db.select_init_monitor()
    
    # 为监控方案获取关键词，使用create模式，最近三个月数据
    search_task_list = await get_keywords(monitor_plans, "最近三个月", num_keywords, 144, 'create')
    
    print("=====获取社会上对热点在各个平台上的看法。=========")
    
    # 初始化关键词数据库连接和爬虫
    search_keywords_db = SearchKeywordsDB()
    # crawlers = MainCrawler(["ks", "douyin", "wb", "zh"], config_obj)  # 初始化快手、抖音、微博、知乎爬虫
    crawlers = MainCrawler(["wb"], config_obj)  # 仅微博爬虫（测试用）
    
    # 初始化爬虫并登录各平台
    await crawlers.init_and_login()
    
    # 初始化进度缓存，用于记录已完成的关键词爬取
    cache = KeywordProgressCache()
    
    # 遍历所有监控方案和对应的关键词
    for monitor_id, search_keywords in search_task_list.items():
        # 获取当前监控方案的详细信息
        tmp_monitor = await monitor_plan_db.select_monitor_by_plan_id(monitor_id)
        
        # 跳过无关键词的监控方案
        if len(search_keywords) == 0:
            continue
        
        # 过滤已完成的关键词，避免重复爬取
        keywords_to_run = [kw for kw in search_keywords[:-1] if not cache.is_done(monitor_id, kw)]
        print(f"当前监控方案 {monitor_id} 待爬取关键词: {keywords_to_run}")
        
        # 遍历所有待爬取关键词
        for keyword in keywords_to_run:
            # 遍历所有爬虫平台
            for platform, crawler in crawlers.crawlers.items():
                # 检查当前平台是否在监控方案的平台列表中
                if judge_platform_contain_relation(platform, tmp_monitor.platform):
                    # 配置爬虫参数
                    crawler.config.MONITOR_PLAN_ID = monitor_id           # 监控方案ID
                    crawler.config.KEYWORDS = keyword                     # 搜索关键词
                    crawler.config.SEARCH_KEYWORD_ID = f"{search_keywords[-1]}-{keyword}"  # 组合搜索关键词ID
                    crawler.config.CRAWLER_MAX_NOTES_COUNT = max_crawler_notes_count  # 最大爬取数量
                    crawler.config.CRAWLER_TYPE = "search"                # 爬取类型为搜索
                    crawler.config.END_PAGE = 4                          # 结束页码
                    crawler.config.ENABLE_GET_SUB_COMMENTS = False       # 不获取子评论
                    crawler.config.START_PAGE = 1                        # 开始页码
                    crawler.config.HEADLESS = False                      # 非无头模式
                    
                    # 启动爬虫
                    await crawler.start()
            
            # 该关键词所有平台爬取完成，标记为已完成
            cache.mark_done(monitor_id, keyword)
            print(f"关键词 {keyword} 所有平台爬取完成，已写入缓存")
        
        # 更新关键词的最后更新时间和间隔
        await search_keywords_db.update_last_update_time_and_interval(
            int(search_keywords[-1]),  # 搜索关键词ID
            datetime_to_bigint(datetime.datetime.now()),  # 当前时间
            24  # 更新间隔（小时）
        )
        
        # 更新监控方案的最后更新时间
        await monitor_plan_db.update_last_update_time(monitor_id, datetime_to_bigint(datetime.datetime.now()))
    
    print("========初始化的方案插入完成了=======")

async def update_monitor_plan(config_obj, number_keywords=5, max_crawler_notes_count=15):
    """
    更新已经初始化的监控方案
    
    功能流程：
    1. 获取所有监控方案
    2. 筛选出需要更新的监控方案（距离上次更新超过监控时间间隔）
    3. 为每个需要更新的方案获取新的关键词（最近几天数据）
    4. 初始化爬虫并登录各平台
    5. 对每个关键词在各平台进行搜索和爬取
    6. 更新关键词和监控方案的最后更新时间
    
    参数:
        config_obj: 配置对象，包含爬虫的基本配置
        number_keywords: int - 每个监控方案获取的关键词数量，默认为5
        max_crawler_notes_count: int - 每个关键词爬取的最大内容数量，默认为15
    """
    # 初始化数据库连接
    monitor_plan_db = MonitorPlanDB()
    
    # 获取所有监控方案
    full_monitor_plans = await monitor_plan_db.select_monitors()
    
    # 筛选出需要更新的监控方案
    monitor_plans = []
    current_time = datetime_to_bigint(datetime.datetime.now())
    
    for monitor_plan in full_monitor_plans:
        # 如果距离上次更新时间超过了监控时间间隔，则需要更新
        if not within_hours(monitor_plan.last_update_time, current_time, monitor_plan.monitor_time_interval):
            monitor_plans.append(monitor_plan)
    
    # 初始化关键词数据库连接
    search_keywords_db = SearchKeywordsDB()
    search_task_list = {}
    
    # 为每个需要更新的方案获取关键词
    for mp in monitor_plans:
        res = await get_keywords([mp], "最近几天", number_keywords, mp.monitor_time_interval, 'update')
        if isinstance(res, dict) and len(res) > 0:
            search_task_list.update(res)
    
    # 初始化爬虫
    crawlers = MainCrawler(["wb", "zh", "ks", "douyin"], config_obj)  # 微博、知乎、快手、抖音
    # crawlers = MainCrawler(["wb"], config_obj)  # 仅微博爬虫（测试用）
    
    # 初始化爬虫并登录各平台
    await crawlers.init_and_login()
    
    # 初始化进度缓存
    cache = KeywordProgressCache()
    
    # 遍历所有监控方案和对应的关键词
    for monitor_id, search_keywords in search_task_list.items():
        # 获取当前监控方案的详细信息
        tmp_monitor = await monitor_plan_db.select_monitor_by_plan_id(monitor_id)
        
        # 跳过无关键词的监控方案
        if len(search_keywords) == 0:
            continue
        
        # 过滤已完成的关键词，避免重复爬取
        keywords_to_run = [kw for kw in search_keywords[:-1] if not cache.is_done(monitor_id, kw)]
        
        # 遍历所有待爬取关键词
        for keyword in keywords_to_run:
            # 遍历所有爬虫平台
            for platform, crawler in crawlers.crawlers.items():
                # 检查当前平台是否在监控方案的平台列表中
                if judge_platform_contain_relation(platform, tmp_monitor.platform):
                    # 配置爬虫参数
                    crawler.config.MONITOR_PLAN_ID = monitor_id           # 监控方案ID
                    crawler.config.KEYWORDS = keyword                     # 搜索关键词
                    crawler.config.SEARCH_KEYWORD_ID = f"{search_keywords[-1]}-{keyword}"  # 组合搜索关键词ID
                    crawler.config.CRAWLER_MAX_NOTES_COUNT = max_crawler_notes_count  # 最大爬取数量
                    crawler.config.CRAWLER_TYPE = "search"                # 爬取类型为搜索
                    crawler.config.END_PAGE = 4                          # 结束页码
                    crawler.config.ENABLE_GET_SUB_COMMENTS = False       # 不获取子评论
                    crawler.config.START_PAGE = 1                        # 开始页码
                    
                    # 启动爬虫
                    await crawler.start()
            
            # 该关键词所有平台爬取完成，标记为已完成
            cache.mark_done(monitor_id, keyword)
        
        # 更新关键词的最后更新时间和间隔
        await search_keywords_db.update_last_update_time_and_interval(
            int(search_keywords[-1]),  # 搜索关键词ID
            datetime_to_bigint(datetime.datetime.now()),  # 当前时间
            24  # 更新间隔（小时）
        )
        
        # 更新监控方案的最后更新时间
        await monitor_plan_db.update_last_update_time(monitor_id, datetime_to_bigint(datetime.datetime.now()))
    
async def update_search_keywords(config_obj, max_crawler_notes_count=10):
    """
    更新搜索关键词
    
    功能流程：
    1. 获取所有搜索关键词
    2. 筛选出需要更新的关键词（距离上次更新超过更新间隔）
    3. 初始化爬虫并登录各平台
    4. 对每个关键词在各平台进行搜索和爬取
    5. 更新关键词的最后更新时间和间隔时间（动态调整）
    
    参数:
        config_obj: 配置对象，包含爬虫的基本配置
        max_crawler_notes_count: int - 每个关键词爬取的最大内容数量，默认为10
    """
    # 初始化数据库连接
    search_keywords_db = SearchKeywordsDB()
    monitor_plan_db = MonitorPlanDB()
    
    # 获取所有搜索关键词
    search_keywords_list = await search_keywords_db.select_all()
    
    # 筛选出需要更新的关键词
    search_task_list = {}
    current_time = datetime_to_bigint(datetime.datetime.now())
    
    for search_keyword in search_keywords_list:
        # 检查是否需要更新（距离上次更新超过更新间隔）
        if not within_hours(search_keyword.last_update_time, current_time, search_keyword.update_interval):
            # 构建任务列表：[关键词列表, search_keyword_id, update_interval]
            keywords = search_keyword.keywords.split(config.KEYWORD_SEPARATOR)
            keywords.append(search_keyword.id)  # 放入search keyword id
            keywords.append(search_keyword.update_interval)  # 放入search interval
            search_task_list[search_keyword.plan_id] = keywords
    
    # 初始化爬虫
    crawlers = MainCrawler(["zh", "wb", "ks", "douyin"], config_obj)  # 知乎、微博、快手、抖音
    # crawlers = MainCrawler(["zh"], config_obj)  # 仅微博爬虫（测试用）
    
    # 初始化爬虫并登录各平台
    await crawlers.init_and_login()
    
    # 初始化进度缓存
    cache = KeywordProgressCache()
    
    # 遍历所有监控方案和对应的关键词
    for monitor_id, search_keywords in search_task_list.items():
        # 获取当前监控方案的详细信息
        tmp_monitor = await monitor_plan_db.select_monitor_by_plan_id(monitor_id)
        
        # 跳过无关键词的监控方案
        if len(search_keywords) == 0:
            continue
        
        # 过滤已完成的关键词（排除最后两个元素：search_keyword_id和update_interval）
        keywords_to_run = [kw for kw in search_keywords[:-2] if not cache.is_done(monitor_id, kw)]
        
        # 遍历所有待爬取关键词
        for keyword in keywords_to_run:
            # 遍历所有爬虫平台
            for platform, crawler in crawlers.crawlers.items():
                # 检查当前平台是否在监控方案的平台列表中
                if judge_platform_contain_relation(platform, tmp_monitor.platform):
                    # 配置爬虫参数
                    crawler.config.MONITOR_PLAN_ID = monitor_id           # 监控方案ID
                    crawler.config.KEYWORDS = keyword                     # 搜索关键词
                    crawler.config.ENABLE_GET_SUB_COMMENTS = False       # 不获取子评论
                    crawler.config.SEARCH_KEYWORD_ID = f"{search_keywords[-2]}-{keyword}"  # 组合搜索关键词ID
                    crawler.config.CRAWLER_MAX_NOTES_COUNT = max_crawler_notes_count  # 最大爬取数量
                    crawler.config.CRAWLER_TYPE = "search"                # 爬取类型为搜索
                    crawler.config.END_PAGE = 4                          # 结束页码
                    crawler.config.START_PAGE = 1                        # 开始页码
                    crawler.config.HEADLESS = False                      # 非无头模式
                    
                    # 启动爬虫
                    await crawler.start()
            
            # 该关键词所有平台爬取完成，标记为已完成
            cache.mark_done(monitor_id, keyword)
        
        # 更新关键词的最后更新时间和间隔时间（动态调整）
        await search_keywords_db.update_last_update_time_and_interval(
            int(search_keywords[-2]),  # 搜索关键词ID
            datetime_to_bigint(datetime.datetime.now()),  # 当前时间
            update_keyword_search_interval(search_keywords[-1])  # 动态调整更新间隔
        )
        
        # 注释：此处不更新监控方案的最后更新时间，仅更新关键词本身
        # await monitor_plan_db.update_last_update_time(monitor_id, datetime_to_bigint(datetime.datetime.now()))
    
       
async def check():
    """
    检查函数（测试用）

    用于测试更新指定监控方案的最后更新时间
    """
    # 初始化数据库连接
    monitor_plan_db = MonitorPlanDB()
    
    # 更新ID为779的监控方案的最后更新时间为当前时间
    await monitor_plan_db.update_last_update_time(
        779,  # 监控方案ID
        datetime_to_bigint(datetime.datetime.now())  # 当前时间
    )

async def main():
    """
    主函数，程序入口点
    
    功能流程：
    1. 解析命令行参数
    2. 如果数据保存选项为数据库，初始化数据库
    3. 配置爬虫参数
    4. 进入无限循环，执行监控任务
    """
    # 解析命令行参数
    config_obj = await cmd_arg.parse_cmd()
    
    # 如果数据保存选项为数据库，初始化数据库
    if config_obj.save_data_option == "db":
        # 显式导入db.py模块，避免与db目录冲突
        import importlib.util
        spec = importlib.util.spec_from_file_location("db_module", "./db.py")
        db_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(db_module)
        await db_module.init_db()
    
    # 配置爬虫参数
    config_obj.ENABLE_CDP_MODE = False  # 禁用CDP模式
    
    # 进入无限循环，执行监控任务
    while True:
        await init_monitor_plan(config_obj)  # 执行初始化监控方案任务
        # await update_monitor_plan(config_obj)  # 执行更新监控方案任务（已注释）
        # await update_search_keywords(config_obj)  # 执行更新搜索关键词任务（已注释）
        # time.sleep(60*5)  # 休眠5分钟（已注释）
    
    # await check()  # 执行检查函数（测试用，已注释）

if __name__ == '__main__':
    """
    程序入口
    """
    try:
        # 获取事件循环并运行主函数
        asyncio.get_event_loop().run_until_complete(main())
    except KeyboardInterrupt:
        # 捕获键盘中断信号，优雅退出程序
        sys.exit()
