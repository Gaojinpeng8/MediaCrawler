from base.base_crawler import AbstractCrawler
from media_platform.douyin import DouYinCrawler
from media_platform.kuaishou import KuaishouCrawler
from media_platform.weibo import WeiboCrawler
from media_platform.xhs import XiaoHongShuCrawler
from media_platform.zhihu import ZhihuCrawler
import time
from social_monitor.utils import clone_config
class CrawlerFactory:
    CRAWLERS = {
        "xhs": XiaoHongShuCrawler,
        "douyin": DouYinCrawler,
        'ks': KuaishouCrawler,
        "wb": WeiboCrawler,
        "zh": ZhihuCrawler,
        "zhihu": ZhihuCrawler,
    }

    @staticmethod
    def create_crawler(platform: str, config: dict) -> AbstractCrawler:
        crawler_class = CrawlerFactory.CRAWLERS.get(platform)
        if not crawler_class:
            raise ValueError("Invalid Media Platform Currently only supported xhs or dy or ks or bili ...")
        # 不同平台的构造函数签名不完全一致：
        # - xhs/douyin 采用 (platform, config)
        # - wb 等部分平台采用 (config)
        if platform in ['wb', 'ks']:
            return crawler_class(config=config)
        return crawler_class(platform, config)

class MainCrawler:
    """
    主爬虫类，主要负责协调不同平台和任务的爬虫。
    """
    def __init__(self, platforn, config):
        self.crawler_factory = CrawlerFactory()
        self.crawlers = {}
        for platform in platforn:
            tmp_config = clone_config(config, PLATFORM=platform)
            self.crawlers[platform] = self.crawler_factory.create_crawler(platform, tmp_config)

        
    async def init_and_login(self):
        for crawler in self.crawlers.values():
            crawler.config.CRAWLER_TYPE = ""
            crawler.config.CRAWLER_MAX_NOTES_COUNT = 100
            crawler.config.ENABLE_GET_SUB_COMMENTS = True # 换成根据一级评论的热度来判断是否需要
            crawler.config.HEADLESS = False
            await crawler.start()
            # time.sleep(5)

    async def search(self, query_keys: list, start_pages, end_pages, max_note_count=100):
        for page in range(start_pages, end_pages+1):
            for platform,crawler in self.crawlers.items():
                crawler.config.CRAWLER_TYPE = "search"
                crawler.config.KEYWORDS = ",".join(query_keys)
                crawler.config.START_PAGE = page
                crawler.config.END_PAGE = page
                crawler.config.CRAWLER_MAX_NOTES_COUNT = max_note_count
                crawler.config.PLATFORM = platform
                await crawler.search(query_keys)
                


