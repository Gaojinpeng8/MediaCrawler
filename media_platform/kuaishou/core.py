# -*- coding: utf-8 -*-
# Copyright (c) 2025 relakkes@gmail.com
#
# This file is part of MediaCrawler project.
# Repository: https://github.com/NanmiCoder/MediaCrawler/blob/main/media_platform/kuaishou/core.py
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


import asyncio
import os
# import random  # Removed as we now use fixed config.CRAWLER_MAX_SLEEP_SEC intervals
import time
from asyncio import Task
from typing import Dict, List, Optional, Tuple

from playwright.async_api import (
    BrowserContext,
    BrowserType,
    Page,
    Playwright,
    async_playwright,
)

import config
from base.base_crawler import AbstractCrawler
from model.m_kuaishou import VideoUrlInfo, CreatorUrlInfo
from proxy.proxy_ip_pool import IpInfoModel, create_ip_pool
from store import kuaishou as kuaishou_store
from tools import utils
from tools.cdp_browser import CDPBrowserManager
from var import comment_tasks_var, crawler_type_var, source_keyword_var

from .client import KuaiShouClient
from .exception import DataFetchError
from .help import parse_video_info_from_url, parse_creator_info_from_url
from .login import KuaishouLogin


class KuaishouCrawler(AbstractCrawler):
    """快手爬虫实现类
    
    继承自AbstractCrawler，实现了快手平台的内容爬取功能，包括：
    - 关键词搜索爬取
    - 指定视频爬取
    - 创作者及其视频爬取
    - 评论获取
    
    属性:
        context_page: Playwright页面对象
        ks_client: 快手API客户端
        browser_context: Playwright浏览器上下文
        cdp_manager: CDP浏览器管理器（可选）
    """
    context_page: Page
    ks_client: KuaiShouClient
    browser_context: BrowserContext
    cdp_manager: Optional[CDPBrowserManager]

    def __init__(self, config: config):
        """初始化快手爬虫
        
        参数:
            config: 爬虫配置对象
        """
        # super().__init__(platform, config)
        self.index_url = "https://www.kuaishou.com"  # 快手首页URL
        self.config = config  # 爬虫配置
        self.user_agent = utils.get_user_agent()  # 获取随机User-Agent
        self.cdp_manager = None  # CDP浏览器管理器，默认为None
        self.ip_proxy_pool = None  # 代理IP池，用于自动刷新代理
        self.logger = utils.get_logger("ks")

    async def start(self):
        """启动快手爬虫
        
        流程:
        1. 初始化代理（如果启用）
        2. 启动浏览器（根据配置选择CDP模式或标准模式）
        3. 创建浏览器页面对象并访问快手首页
        4. 初始化快手API客户端
        5. 登录快手（如果需要）
        6. 根据配置的爬虫类型执行不同的爬取任务
        """
        playwright_proxy_format, httpx_proxy_format = None, None
        
        # 初始化代理IP池（如果启用）
        if config.ENABLE_IP_PROXY:
            self.ip_proxy_pool = await create_ip_pool(
                config.IP_PROXY_POOL_COUNT, enable_validate_ip=True
            )
            ip_proxy_info: IpInfoModel = await self.ip_proxy_pool.get_proxy()
            playwright_proxy_format, httpx_proxy_format = utils.format_proxy_info(
                ip_proxy_info
            )

        # 启动Playwright
        async with async_playwright() as playwright:
            # 根据配置选择浏览器启动模式
            if self.config.ENABLE_CDP_MODE:
                utils.logger.info("[KuaishouCrawler] Launching browser using CDP mode")
                self.browser_context = await self.launch_browser_with_cdp(
                    playwright,
                    playwright_proxy_format,
                    self.user_agent,
                    headless=self.config.CDP_HEADLESS,
                )
            else:
                utils.logger.info("[KuaishouCrawler] Launching browser using standard mode")
                # 启动浏览器上下文
                chromium = playwright.chromium
                self.browser_context = await self.launch_browser(
                    chromium, None, self.user_agent, headless=self.config.HEADLESS
                )
            # 添加stealth.min.js脚本防止网站检测到爬虫
            await self.browser_context.add_init_script(path="libs/stealth.min.js")

            # 创建新的浏览器页面对象并访问快手首页
            self.context_page = await self.browser_context.new_page()
            await self.context_page.goto(f"{self.index_url}?isHome=1")

            # 创建快手API客户端
            self.ks_client = await self.create_ks_client(httpx_proxy_format)
            
            # 检查客户端连接状态，如果未连接则登录
            if not await self.ks_client.pong():
                login_obj = KuaishouLogin(
                    login_type=self.config.LOGIN_TYPE,
                    login_phone=httpx_proxy_format,
                    browser_context=self.browser_context,
                    context_page=self.context_page,
                    cookie_str=self.config.COOKIES,
                )
                await login_obj.begin()
                await self.ks_client.update_cookies(
                    browser_context=self.browser_context
                )

            # 设置爬虫类型上下文变量
            crawler_type_var.set(self.config.CRAWLER_TYPE)
            
            # 设置爬虫类型
            # crawler_type_var.set(getattr(self.config, 'CRAWLER_TYPE', 'search'))
            crawler_type_var.set(self.config.CRAWLER_TYPE)
            if self.config.CRAWLER_TYPE == "search":
                # Search for videos and retrieve their comment information.
                self.logger.info("调用快手爬虫关键词搜索功能")
                await self.search(getattr(self.config, 'KEYWORDS', '').split(","))
            elif self.config.CRAWLER_TYPE == "detail":
                # Get the information and comments of the specified post
                await self.get_specified_videos()
            elif self.config.CRAWLER_TYPE == "hotlist":
                # Get hot title
                self.logger.info("调用快手爬虫热榜获取功能")
                await self.get_hotlist()
            elif self.config.CRAWLER_TYPE == "hotlist_detail": 
                # Get hotlist contents
                self.logger.info("调用快手爬虫获取热榜具体信息功能")
                await self.get_hotlist_video()
            elif self.config.CRAWLER_TYPE == "update":
                # Update contents and comments between chosen date
                self.logger.info("调用快手爬虫更新功能")
                await self.update()
            else:
                pass
            self.logger.info("快手爬取结束")
            # 根据爬虫类型执行不同的爬取任务
            # if config.CRAWLER_TYPE == "search":
            #     # 执行关键词搜索爬取
            #     await self.search()
            # elif config.CRAWLER_TYPE == "detail":
            #     # 获取指定视频的信息和评论
            #     await self.get_specified_videos()
            # elif config.CRAWLER_TYPE == "creator":
            #     # 获取创作者信息及其视频和评论
            #     await self.get_creators_and_videos()
            # else:
            #     pass

            utils.logger.info("[KuaishouCrawler.start] Kuaishou Crawler finished ...")

    async def search(self, keywords: List[str]):
        """关键词搜索爬取
        
        根据配置的关键词列表在快手上搜索相关视频，
        并爬取视频信息和评论。
        """
        utils.logger.info("[KuaishouCrawler.search] Begin search kuaishou keywords")
        ks_limit_count = 10  # 快手每页固定显示20个视频
        
        # 确保爬取数量不小于每页限制
        if self.config.CRAWLER_MAX_NOTES_COUNT < ks_limit_count:
            self.config.CRAWLER_MAX_NOTES_COUNT = ks_limit_count
            
        start_page = self.config.START_PAGE
        self.logger.info(f"开始搜索快手关键词，配置: start_page={start_page}, end_page={self.config.END_PAGE}, max_notes={self.config.CRAWLER_MAX_NOTES_COUNT}, limit_count={ks_limit_count}")
        # 遍历所有关键词
        for keyword in keywords:
            search_session_id = ""  # 搜索会话ID
            source_keyword_var.set(keyword)  # 设置当前搜索关键词上下文变量
            utils.logger.info(
                f"[KuaishouCrawler.search] Current search keyword: {keyword}"
            )
            
            page = 1
            
            # 循环爬取直到达到最大爬取数量
            while (
                page - start_page + 1
            ) * ks_limit_count <= self.config.CRAWLER_MAX_NOTES_COUNT:
                # 跳过起始页之前的页面
                if page < start_page:
                    utils.logger.info(f"[KuaishouCrawler.search] Skip page: {page}")
                    page += 1
                    continue
                
                utils.logger.info(
                    f"[KuaishouCrawler.search] search kuaishou keyword: {keyword}, page: {page}"
                )
                video_id_list: List[str] = []  # 存储当前页面的视频ID列表
                
                # 使用API客户端搜索关键词相关视频
                videos_res = await self.ks_client.search_info_by_keyword(
                    keyword=keyword,
                    pcursor=str(page),
                    search_session_id=search_session_id,
                )
                
                # 检查搜索结果
                if not videos_res:
                    utils.logger.error(
                        f"[KuaishouCrawler.search] search info by keyword:{keyword} not found data"
                    )
                    continue

                vision_search_photo: Dict = videos_res.get("visionSearchPhoto")

                if not vision_search_photo:
                    self.logger.error(f"快手爬虫搜索关键词{keyword}页面{page}返回数据格式异常，增加页码到{page+1}")
                    page += 1
                    continue

                if vision_search_photo.get("result") != 1:
                    utils.logger.error(
                        f"[KuaishouCrawler.search] search info by keyword:{keyword} not found data "
                    )
                    page += 1
                    continue
                
                # 更新搜索会话ID
                search_session_id = vision_search_photo.get("searchSessionId", "")
                feeds = vision_search_photo.get("feeds", [])
                
                if not feeds:
                    self.logger.warning(f"快手爬虫搜索关键词{keyword}页面{page}未获取到视频数据，增加页码到{page+1}")
                    page += 1
                    continue

                # # 处理搜索结果中的视频信息
                # for video_detail in vision_search_photo.get("feeds"):
                #     video_id_list.append(video_detail.get("photo", {}).get("id"))
                #     # 保存视频信息到存储
                #     await kuaishou_store.update_kuaishou_video(video_item=video_detail)
                for video_detail in feeds:
                    if not video_detail:
                        continue
                        
                    photo_info = video_detail.get("photo", {})
                    if not photo_info:
                        continue
                        
                    video_id = photo_info.get("id")
                    if video_id:
                        video_id_list.append(video_id)
                        await kuaishou_store.update_kuaishou_video(video_item=video_detail, config=self.config)

                # 批量获取视频评论
                page += 1

                # 页面导航后休眠，避免请求过于频繁
                await asyncio.sleep(config.CRAWLER_MAX_SLEEP_SEC)
                utils.logger.info(f"[KuaishouCrawler.search] Sleeping for {config.CRAWLER_MAX_SLEEP_SEC} seconds after page {page-1}")

                # 批量获取当前页面所有视频的评论
                await self.batch_get_video_comments(video_id_list)

    async def get_specified_videos(self):
        """获取指定视频的信息和评论
        
        根据配置的视频URL列表，解析视频ID并获取视频详细信息和评论。
        """
        utils.logger.info("[KuaishouCrawler.get_specified_videos] Parsing video URLs...")
        video_ids = []  # 存储解析后的视频ID列表
        
        # 遍历配置中的视频URL列表
        for video_url in config.KS_SPECIFIED_ID_LIST:
            try:
                # 解析视频URL获取视频信息
                video_info = parse_video_info_from_url(video_url)
                video_ids.append(video_info.video_id)
                utils.logger.info(f"Parsed video ID: {video_info.video_id} from {video_url}")
            except ValueError as e:
                utils.logger.error(f"Failed to parse video URL: {e}")
                continue

        # 创建信号量控制并发数
        semaphore = asyncio.Semaphore(config.MAX_CONCURRENCY_NUM)
        
        # 创建视频信息获取任务列表
        task_list = [
            self.get_video_info_task(video_id=video_id, semaphore=semaphore)
            for video_id in video_ids
        ]
        
        # 并发获取视频信息
        video_details = await asyncio.gather(*task_list)
        
        # 保存视频信息
        for video_detail in video_details:
            if video_detail is not None:
                await kuaishou_store.update_kuaishou_video(video_detail)
        
        # 批量获取视频评论
        await self.batch_get_video_comments(video_ids)

    async def get_video_info_task(
        self, video_id: str, semaphore: asyncio.Semaphore
    ) -> Optional[Dict]:
        """获取视频详细信息的异步任务
        
        参数:
            video_id: 视频ID
            semaphore: 并发控制信号量
            
        返回:
            视频详细信息字典，如果获取失败则返回None
        """
        async with semaphore:
            try:
                # 使用API客户端获取视频详细信息
                result = await self.ks_client.get_video_info(video_id)

                # 获取视频详情后休眠，避免请求过于频繁
                await asyncio.sleep(config.CRAWLER_MAX_SLEEP_SEC)
                utils.logger.info(f"[KuaishouCrawler.get_video_info_task] Sleeping for {config.CRAWLER_MAX_SLEEP_SEC} seconds after fetching video details {video_id}")

                utils.logger.info(
                    f"[KuaishouCrawler.get_video_info_task] Get video_id:{video_id} info result: {result} ..."
                )
                
                # 返回视频详情信息
                return result.get("visionVideoDetail")
            except DataFetchError as ex:
                utils.logger.error(
                    f"[KuaishouCrawler.get_video_info_task] Get video detail error: {ex}"
                )
                return None
            except KeyError as ex:
                utils.logger.error(
                    f"[KuaishouCrawler.get_video_info_task] have not fund video detail video_id:{video_id}, err: {ex}"
                )
                return None

    async def batch_get_video_comments(self, video_id_list: List[str]):
        """批量获取视频评论
        
        参数:
            video_id_list: 视频ID列表
        """
        # 检查是否启用评论爬取
        if not config.ENABLE_GET_COMMENTS:
            utils.logger.info(
                f"[KuaishouCrawler.batch_get_video_comments] Crawling comment mode is not enabled"
            )
            return

        utils.logger.info(
            f"[KuaishouCrawler.batch_get_video_comments] video ids:{video_id_list}"
        )
        
        # 创建信号量控制并发数
        semaphore = asyncio.Semaphore(config.MAX_CONCURRENCY_NUM)
        
        # 创建评论获取任务列表
        task_list: List[Task] = []
        for video_id in video_id_list:
            task = asyncio.create_task(
                self.get_comments(video_id, semaphore), name=video_id
            )
            task_list.append(task)

        # 设置评论任务上下文变量
        comment_tasks_var.set(task_list)
        
        # 并发获取所有视频的评论
        await asyncio.gather(*task_list)

    async def get_comments(self, video_id: str, semaphore: asyncio.Semaphore):
        """获取单个视频的评论
        
        参数:
            video_id: 视频ID
            semaphore: 并发控制信号量
        """
        async with semaphore:
            try:
                utils.logger.info(
                    f"[KuaishouCrawler.get_comments] begin get video_id: {video_id} comments ..."
                )

                # 获取评论前休眠，避免请求过于频繁
                await asyncio.sleep(config.CRAWLER_MAX_SLEEP_SEC)
                utils.logger.info(f"[KuaishouCrawler.get_comments] Sleeping for {config.CRAWLER_MAX_SLEEP_SEC} seconds before fetching comments for video {video_id}")

                # 获取视频的所有评论
                await self.ks_client.get_video_all_comments(
                    photo_id=video_id,
                    crawl_interval=config.CRAWLER_MAX_SLEEP_SEC,
                    callback=kuaishou_store.batch_update_ks_video_comments,
                    max_count=self.config.CRAWLER_MAX_COMMENTS_COUNT_SINGLENOTES,
                )
            except DataFetchError as ex:
                utils.logger.error(
                    f"[KuaishouCrawler.get_comments] get video_id: {video_id} comment error: {ex}"
                )
            except Exception as e:
                utils.logger.error(
                    f"[KuaishouCrawler.get_comments] may be been blocked, err:{e}"
                )
                # 可能被快手屏蔽了请求，取消当前所有评论任务
                current_running_tasks = comment_tasks_var.get()
                for task in current_running_tasks:
                    task.cancel()
                
                # 休眠20秒后重新访问首页并更新cookie
                time.sleep(20)
                await self.context_page.goto(f"{self.index_url}?isHome=1")
                await self.ks_client.update_cookies(
                    browser_context=self.browser_context
                )

    async def create_ks_client(self, httpx_proxy: Optional[str]) -> KuaiShouClient:
        """创建快手API客户端
        
        参数:
            httpx_proxy: HTTP代理格式
            
        返回:
            KuaiShouClient对象
        """
        utils.logger.info(
            "[KuaishouCrawler.create_ks_client] Begin create kuaishou API client ..."
        )
        
        # 从浏览器上下文获取并转换cookies
        cookie_str, cookie_dict = utils.convert_cookies(
            await self.browser_context.cookies()
        )
        cookie_dict = utils.route_cookie("ks", cookie_dict)
        cookie_str = utils.cookie_dict_to_str(cookie_dict)
        # 创建快手API客户端实例
        ks_client_obj = KuaiShouClient(
            proxy=httpx_proxy,
            headers={
                "User-Agent": self.user_agent,
                "Cookie": cookie_str,
                "Origin": self.index_url,
                "Referer": self.index_url,
                "Content-Type": "application/json;charset=UTF-8",
            },
            playwright_page=self.context_page,
            cookie_dict=cookie_dict,
            proxy_ip_pool=self.ip_proxy_pool,  # 传递代理池用于自动刷新
            config=self.config,
        )
        return ks_client_obj

    async def launch_browser(
        self,
        chromium: BrowserType,
        playwright_proxy: Optional[Dict],
        user_agent: Optional[str],
        headless: bool = True,
    ) -> BrowserContext:
        """启动浏览器并创建浏览器上下文
        
        参数:
            chromium: Chromium浏览器类型
            playwright_proxy: Playwright代理格式
            user_agent: 用户代理字符串
            headless: 是否无头模式
            
        返回:
            BrowserContext对象
        """
        utils.logger.info(
            "[KuaishouCrawler.launch_browser] Begin create browser context ..."
        )
        
        # 检查是否保存登录状态
        if config.SAVE_LOGIN_STATE:
            # 创建持久化浏览器上下文目录
            user_data_dir = os.path.join(
                os.getcwd(), "browser_data", config.USER_DATA_DIR % config.PLATFORM
            )  # type: ignore
            
            # 启动持久化浏览器上下文
            browser_context = await chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                accept_downloads=True,
                headless=headless,
                proxy=playwright_proxy,  # type: ignore
                viewport={"width": 1920, "height": 1080},
                user_agent=user_agent,
                channel="chrome",  # 使用系统的稳定Chrome版本
            )
            return browser_context
        else:
            # 启动临时浏览器
            browser = await chromium.launch(headless=headless, proxy=playwright_proxy, channel="chrome")  # type: ignore
            
            # 创建新的浏览器上下文
            browser_context = await browser.new_context(
                viewport={"width": 1920, "height": 1080}, user_agent=user_agent
            )
            return browser_context

    async def launch_browser_with_cdp(
        self,
        playwright: Playwright,
        playwright_proxy: Optional[Dict],
        user_agent: Optional[str],
        headless: bool = True,
    ) -> BrowserContext:
        """使用CDP模式启动浏览器
        
        参数:
            playwright: Playwright实例
            playwright_proxy: Playwright代理格式
            user_agent: 用户代理字符串
            headless: 是否无头模式
            
        返回:
            BrowserContext对象
        """
        try:
            # 初始化CDP浏览器管理器
            self.cdp_manager = CDPBrowserManager()
            
            # 启动并连接CDP浏览器
            browser_context = await self.cdp_manager.launch_and_connect(
                playwright=playwright,
                playwright_proxy=playwright_proxy,
                user_agent=user_agent,
                headless=headless,
            )

            # 显示浏览器信息
            browser_info = await self.cdp_manager.get_browser_info()
            utils.logger.info(f"[KuaishouCrawler] CDP browser info: {browser_info}")

            return browser_context

        except Exception as e:
            utils.logger.error(
                f"[KuaishouCrawler] CDP mode launch failed, fallback to standard mode: {e}"
            )
            # CDP模式失败，回退到标准模式
            chromium = playwright.chromium
            return await self.launch_browser(
                chromium, playwright_proxy, user_agent, headless
            )

    async def get_creators_and_videos(self) -> None:
        """获取创作者信息及其视频和评论
        
        根据配置的创作者URL列表，获取创作者详细信息、视频列表及视频评论。
        """
        utils.logger.info(
            "[KuaiShouCrawler.get_creators_and_videos] Begin get kuaishou creators"
        )
        
        # 遍历配置中的创作者URL列表
        for creator_url in config.KS_CREATOR_ID_LIST:
            try:
                # 解析创作者URL获取用户ID
                creator_info: CreatorUrlInfo = parse_creator_info_from_url(creator_url)
                utils.logger.info(f"[KuaiShouCrawler.get_creators_and_videos] Parse creator URL info: {creator_info}")
                user_id = creator_info.user_id

                # 从网页内容获取创作者详细信息
                createor_info: Dict = await self.ks_client.get_creator_info(user_id=user_id)
                if createor_info:
                    await kuaishou_store.save_creator(user_id, creator=createor_info)
            except ValueError as e:
                utils.logger.error(f"[KuaiShouCrawler.get_creators_and_videos] Failed to parse creator URL: {e}")
                continue

            # Get all video information of the creator
            all_video_list = await self.ks_client.get_all_videos_by_creator(
                user_id=user_id,
                crawl_interval=config.CRAWLER_MAX_SLEEP_SEC,
                callback=self.fetch_creator_video_detail,
            )

            video_ids = [
                video_item.get("photo", {}).get("id") for video_item in all_video_list
            ]
            await self.batch_get_video_comments(video_ids)

    async def fetch_creator_video_detail(self, video_list: List[Dict]):
        """
        Concurrently obtain the specified post list and save the data
        """
        semaphore = asyncio.Semaphore(config.MAX_CONCURRENCY_NUM)
        task_list = [
            self.get_video_info_task(post_item.get("photo", {}).get("id"), semaphore)
            for post_item in video_list
        ]

        video_details = await asyncio.gather(*task_list)
        for video_detail in video_details:
            if video_detail is not None:
                await kuaishou_store.update_kuaishou_video(video_detail)

    async def close(self):
        """Close browser context"""
        # If using CDP mode, need special handling
        if self.cdp_manager:
            await self.cdp_manager.cleanup()
            self.cdp_manager = None
        else:
            await self.browser_context.close()
        utils.logger.info("[KuaishouCrawler.close] Browser context closed ...")
