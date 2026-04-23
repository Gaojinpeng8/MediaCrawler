# 并发爬取关键词设计

## 问题

`init_monitor_plan` 中关键词爬取是三重嵌套串行循环（方案 → 关键词 → 平台），每个 `crawler.start()` 是完整浏览器会话（几十秒到几分钟），总耗时 = 方案数 × 关键词数 × 平台数 × 单次时间。

## 目标

仅改造 `init_monitor_plan` 函数，使同一方案下多个关键词并发爬取，单关键词的各平台仍串行。

## 方案

使用 `asyncio.Semaphore(5)` + `asyncio.gather` 实现关键词级并发。

### 核心变更

1. 将"爬取单个关键词"逻辑抽取为 `async def _crawl_single_keyword(...)`
2. 外层循环用 `asyncio.gather` 并发执行所有关键词任务
3. 通过 `asyncio.Semaphore(5)` 限制同时最多 5 个关键词爬取
4. 使用 `clone_config` 为每个关键词任务创建独立配置，避免共享 `crawler.config` 竞争

### 不改动的部分

- `update_monitor_plan` 和 `update_search_keywords` 保持原串行逻辑
- 关键词过滤（`cache.is_done`）逻辑不变
- 爬取完成后的 DB 更新逻辑不变
- 平台遍历顺序不变

## 风险

- 5 个并发意味着最多同时打开 5 个浏览器实例，需确保机器内存和 CPU 足够
- 并发数可通过修改 `MAX_KEYWORD_CONCURRENCY` 常量调整
