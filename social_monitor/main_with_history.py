import asyncio
import sys
sys.path.append("./")
from social_monitor.main_crawler import MainCrawler
import cmd_arg
import asyncio
import sys
from schema.async_db import MonitorPlanDB, SearchKeywordsDB
from schema import SearchKeywordsEntity, MonitorPlanEntity
from social_monitor.mcp_client import KIMISearch, BAIDUSearch
from social_monitor.utils import datetime_to_bigint, within_hours, judge_platform_contain_relation, update_keyword_search_interval
from social_monitor.src.progress_cache import KeywordProgressCache
import datetime
import config
from social_monitor.history_stats_calculator import HistoryStatsCalculator

async def get_keywords(monitor_plans: list[MonitorPlanEntity], time_range="最近三个月的", nums=10, monitor_time_interval=24, check_node=None) -> list:
    if check_node == None or check_node not in ['create', 'update']:
        return
    # 去获取方案对应的关键词。 存在两种情况，一种是获取刚刚插入的init的keywords，还有一种是正常获取关键词。
    search_keywords_db = SearchKeywordsDB()
    search_tools = [KIMISearch(), BAIDUSearch()]
    search_task_list = {}
    for monitor_plan in monitor_plans:
        search_keywords_entity = await search_keywords_db.get_by_plan_id(monitor_plan.plan_id)
        # 若已存在关键词记录且仍在时间间隔内，则直接复用
        if search_keywords_entity:
            check_time = (
                search_keywords_entity.create_time if check_node == 'create'
                else search_keywords_entity.last_update_time
            )
            if within_hours(check_time, datetime_to_bigint(datetime.datetime.now()), monitor_time_interval):
                search_task_list[monitor_plan.plan_id] = (
                    search_keywords_entity.keywords.split(config.KEYWORD_SEPARATOR) + [search_keywords_entity.id]
                )
                continue
        for search_tool in search_tools:
            keyworks = search_tool.search_init_monitor(monitor_plan, time_range, nums)
            if search_task_list.get(monitor_plan.plan_id) is None:
                search_task_list[monitor_plan.plan_id] = []
            search_task_list[monitor_plan.plan_id].extend([word for word in keyworks if len(word.strip()) > 0])
        if len(search_task_list[monitor_plan.plan_id]) == 0:
            continue
        search_keyword_id = await search_keywords_db.insert(SearchKeywordsEntity(
            create_time=datetime_to_bigint(datetime.datetime.now()),
            plan_id=monitor_plan.plan_id,
            keywords=config.KEYWORD_SEPARATOR.join(search_task_list[monitor_plan.plan_id])
        ))
        search_task_list[monitor_plan.plan_id].append(search_keyword_id)
    return search_task_list
    
async def calculate_and_save_history_stats(search_keywords_entity: SearchKeywordsEntity):
    """计算并保存历史统计信息"""
    calculator = HistoryStatsCalculator()
    
    print(f"开始计算关键词 '{search_keywords_entity.keywords}' 的历史统计信息...")
    
    try:
        # 计算统计信息
        stats = await calculator.calculate_stats_by_search_keyword(search_keywords_entity)
        
        if stats:
            # 保存统计信息
            saved_id = await calculator.save_history_stats(stats)
            print(f"历史统计信息计算完成并保存，ID: {saved_id}")
            
            # 打印统计摘要
            print(f"统计摘要:")
            print(f"  - 总帖子数: {stats.total_posts}")
            print(f"  - 总浏览量: {stats.total_views}")
            print(f"  - 总点赞数: {stats.total_likes}")
            print(f"  - 正向评论: {stats.positive_comments}")
            print(f"  - 负向评论: {stats.negative_comments}")
            print(f"  - 中性评论: {stats.neutral_comments}")
            print(f"  - 正向帖子: {stats.positive_posts}")
            print(f"  - 负向帖子: {stats.negative_posts}")
            print(f"  - 中性帖子: {stats.neutral_posts}")
            
            return saved_id
        else:
            print("统计信息计算失败")
            return None
            
    except Exception as e:
        print(f"计算历史统计信息时出错: {e}")
        import traceback
        traceback.print_exc()
        return None

async def init_monitor_plan(config_obj, num_keywords=15, max_crawler_notes_count=15):
    print("======获取社会热点事件========")
    monitor_plan_db = MonitorPlanDB()
    monitor_plans = await monitor_plan_db.select_init_monitor()
    search_task_list = await get_keywords(monitor_plans, "最近三个月", num_keywords, 144, 'create') # 获取最新的100个事件
    
    print("=====获取社会上对热点在各个平台上的看法。=========")
    search_keywords_db = SearchKeywordsDB()
    crawlers = MainCrawler(["ks", "douyin","wb", "zh"], config_obj)
    # crawlers = MainCrawler(["wb"], config_obj)
    await crawlers.init_and_login()
    cache = KeywordProgressCache()
    
    for monitor_id, search_keywords in search_task_list.items():
        tmp_monitor = await monitor_plan_db.select_monitor_by_plan_id(monitor_id)
        if len(search_keywords) == 0:
            continue
        # 过滤已完成的关键词，避免重复爬取
        keywords_to_run = [kw for kw in search_keywords[:-1] if not cache.is_done(monitor_id, kw)]
        print(keywords_to_run)
        for keyword in keywords_to_run:
            for platform, crawler in crawlers.crawlers.items():
                if judge_platform_contain_relation(platform, tmp_monitor.platform):
                    crawler.config.MONITOR_PLAN_ID = monitor_id
                    crawler.config.KEYWORDS = keyword
                    crawler.config.SEARCH_KEYWORD_ID = str(search_keywords[-1]) + "-" + keyword
                    crawler.config.CRAWLER_MAX_NOTES_COUNT = max_crawler_notes_count
                    crawler.config.CRAWLER_TYPE = "search"
                    crawler.config.END_PAGE = 4
                    crawler.config.ENABLE_GET_SUB_COMMENTS=False
                    crawler.config.START_PAGE = 1
                    crawler.config.HEADLESS = False
                    await crawler.start()
            # 该关键词所有平台与页数均执行完成，写入完成缓存
            cache.mark_done(monitor_id, keyword)
            print(f"关键词 {keyword} 所有平台与页数均执行完成，写入完成缓存")
        
        # 计算并保存历史统计信息
        search_keywords_entity = await search_keywords_db.get_by_id(int(search_keywords[-1]))
        if search_keywords_entity:
            await calculate_and_save_history_stats(search_keywords_entity)
        
        await search_keywords_db.update_last_update_time_and_interval(int(search_keywords[-1]), datetime_to_bigint(datetime.datetime.now()), 24)
        await monitor_plan_db.update_last_update_time(monitor_id, datetime_to_bigint(datetime.datetime.now()))
    print("========初始化的方案插入完成了=======")

async def update_monitor_plan(config_obj, number_keywords=5, max_crawler_notes_count=15):
    """
    更新已经初始化的方案。包括两个方向。
    - 一个是通过AI搜索获取词，然后进行爬取。
    - 对于现有的词，也进行爬取，但是爬取的数量少一些。然后把更新时间往后推。
    """
    monitor_plan_db = MonitorPlanDB()
    full_monitor_plans = await monitor_plan_db.select_monitors()
    monitor_plans = []
    for monitor_plan in full_monitor_plans:
        if not within_hours(monitor_plan.last_update_time, datetime_to_bigint(datetime.datetime.now()), monitor_plan.monitor_time_interval): # 如果距离上次更新时间超过了监控时间间隔，那么就需要更新。
            monitor_plans.append(monitor_plan)
    search_keywords_db = SearchKeywordsDB()
    search_task_list = {}
    for mp in monitor_plans:
        res = await get_keywords([mp], "最近几天", number_keywords, mp.monitor_time_interval, 'update')
        if isinstance(res, dict) and len(res) > 0:
            search_task_list.update(res)

    crawlers = MainCrawler(["wb", "zh", "ks", "douyin"], config_obj)
    # crawlers = MainCrawler(["wb"], config_obj)
    await crawlers.init_and_login()
    cache = KeywordProgressCache()
    for monitor_id, search_keywords in search_task_list.items():
        tmp_monitor = await monitor_plan_db.select_monitor_by_plan_id(monitor_id)
        if len(search_keywords) == 0:
            continue
        # 跳过已完成的关键词
        keywords_to_run = [kw for kw in search_keywords[:-1] if not cache.is_done(monitor_id, kw)]
        for keyword in keywords_to_run:
            for platform, crawler in crawlers.crawlers.items():
                if judge_platform_contain_relation(platform, tmp_monitor.platform):
                    crawler.config.MONITOR_PLAN_ID = monitor_id
                    crawler.config.KEYWORDS = keyword
                    crawler.config.SEARCH_KEYWORD_ID = str(search_keywords[-1]) + "-" + keyword
                    crawler.config.CRAWLER_MAX_NOTES_COUNT = max_crawler_notes_count
                    crawler.config.CRAWLER_TYPE = "search"
                    crawler.config.END_PAGE = 4
                    crawler.config.ENABLE_GET_SUB_COMMENTS=False
                    crawler.config.START_PAGE = 1
                    await crawler.start()
            # 该关键词跨平台与分页完成后，写入完成标记
            cache.mark_done(monitor_id, keyword)
        
        # 计算并保存历史统计信息
        search_keywords_entity = await search_keywords_db.get_by_id(int(search_keywords[-1]))
        if search_keywords_entity:
            await calculate_and_save_history_stats(search_keywords_entity)
        
        await search_keywords_db.update_last_update_time_and_interval(int(search_keywords[-1]), datetime_to_bigint(datetime.datetime.now()), 24)
        await monitor_plan_db.update_last_update_time(monitor_id, datetime_to_bigint(datetime.datetime.now()))
    
async def update_search_keywords(config_obj, max_crawler_notes_count=10):
    """
    更新搜索关键词的最后更新时间和间隔时间。
    """
    search_keywords_db = SearchKeywordsDB()
    monitor_plan_db = MonitorPlanDB()
    search_keywords = await search_keywords_db.select_all()
    search_task_list = {}
    for search_keyword in search_keywords:
        if not within_hours(search_keyword.last_update_time, datetime_to_bigint(datetime.datetime.now()), search_keyword.update_interval):
            search_task_list[search_keyword.plan_id] = search_keyword.keywords.split(config.KEYWORD_SEPARATOR)
            search_task_list[search_keyword.plan_id].append(search_keyword.id) # 放入search keyword id
            search_task_list[search_keyword.plan_id].append(search_keyword.update_interval) # 放入search interval
    
    crawlers = MainCrawler(["zh", "wb", "ks", "douyin"], config_obj)
    # crawlers = MainCrawler(["wb"], config_obj)
    await crawlers.init_and_login()
    cache = KeywordProgressCache()
    for monitor_id, search_keywords in search_task_list.items():
        tmp_monitor = await monitor_plan_db.select_monitor_by_plan_id(monitor_id)
        if len(search_keywords) == 0:
            continue
        # 跳过已完成的关键词
        keywords_to_run = [kw for kw in search_keywords[:-2] if not cache.is_done(monitor_id, kw)]
        for keyword in keywords_to_run:
            for platform, crawler in crawlers.crawlers.items():
                if judge_platform_contain_relation(platform, tmp_monitor.platform):
                    crawler.config.MONITOR_PLAN_ID = monitor_id
                    crawler.config.KEYWORDS = keyword
                    crawler.config.ENABLE_GET_SUB_COMMENTS=False
                    crawler.config.SEARCH_KEYWORD_ID = str(search_keywords[-2]) + "-" + keyword
                    crawler.config.CRAWLER_MAX_NOTES_COUNT = max_crawler_notes_count
                    crawler.config.CRAWLER_TYPE = "search"
                    crawler.config.END_PAGE = 4
                    crawler.config.START_PAGE = 1
                    crawler.config.HEADLESS = False
                    await crawler.start()
            # 该关键词跨平台与分页完成后，写入完成标记
            cache.mark_done(monitor_id, keyword)
        
        # 计算并保存历史统计信息
        search_keywords_entity = await search_keywords_db.get_by_id(int(search_keywords[-2]))
        if search_keywords_entity:
            await calculate_and_save_history_stats(search_keywords_entity)
        
        await search_keywords_db.update_last_update_time_and_interval(int(search_keywords[-2]), datetime_to_bigint(datetime.datetime.now()), update_keyword_search_interval(search_keywords[-1]))
        # await monitor_plan_db.update_last_update_time(monitor_id, datetime_to_bigint(datetime.datetime.now()))
    
       
async def check():
    monitor_plan_db = MonitorPlanDB()
    monitor_plans = await monitor_plan_db.update_last_update_time(779,datetime_to_bigint(datetime.datetime.now()))

async def main():
    config_obj = await cmd_arg.parse_cmd()
    if config_obj.SAVE_DATA_OPTION == "db":
        # 显式导入db.py模块，避免与db目录冲突
        import importlib.util
        spec = importlib.util.spec_from_file_location("db_module", "./db.py")
        db_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(db_module)
        await db_module.init_db()
    config_obj.ENABLE_CDP_MODE = False
    while True:
        await init_monitor_plan(config_obj)
        # await update_monitor_plan(config_obj)
        # await update_search_keywords(config_obj)
        # time.sleep(60*5)
    # await check()

if __name__ == '__main__':
    try:
        asyncio.get_event_loop().run_until_complete(main())
    except KeyboardInterrupt:
        sys.exit()