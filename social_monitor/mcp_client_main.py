
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

async def get_keywords(monitor_plans: list[MonitorPlanEntity], time_range="最近三个月的", nums=10, monitor_time_interval=24, check_node=None) -> list:
    if check_node == None or check_node not in ['create', 'update']:
        return
    # 去获取方案对应的关键词。 存在两种情况，一种是获取刚刚插入的init的keywords，还有一种是正常获取关键词。
    search_keywords_db = SearchKeywordsDB()
    search_tools = [KIMISearch(), BAIDUSearch()]
    search_task_list = {}
    for monitor_plan in monitor_plans[:10]:
        search_keywords_entity = await search_keywords_db.get_by_plan_id(monitor_plan.plan_id) # 查询现有的关键词记录
        # 若已存在关键词记录且仍在时间间隔内，则直接复用
        if search_keywords_entity:
            pass
        for search_tool in search_tools:
            keyworks = search_tool.search_init_monitor(monitor_plan, time_range, nums)
            if search_task_list.get(monitor_plan.plan_id) is None:
                search_task_list[monitor_plan.plan_id] = []
            search_task_list[monitor_plan.plan_id].extend([word for word in keyworks if len(word.strip()) > 0])
    return search_task_list


async def init_monitor_plan(config_obj, num_keywords=15, max_crawler_notes_count=15):
    print("======获取社会热点事件========")
    monitor_plan_db = MonitorPlanDB()
    monitor_plans = await monitor_plan_db.select_monitors()
    search_task_list = await get_keywords(monitor_plans, "最近三个月", num_keywords, 144, 'create') # 获取最新的100个事件


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
