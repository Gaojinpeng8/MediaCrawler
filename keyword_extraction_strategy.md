# 关键词提取策略说明

## 目标与范围
- 针对监测方案（`monitor_plan`）生成可用于检索的“时间线关键词”短语。
- 覆盖同一事件的不同阶段，避免集中于单一时间点。

## 数据来源
- 方案列表：从数据库表 `monitor_plan` 读取 `social_monitor/schema/async_db/monitor_db.py:21-24`。
- 方案字段：`plan_id`、`plan_name`、`keywords`（可作为提示词上下文）。

## 主流程
- 仅输出模式入口：`output_first_n_timeline_keywords` 与 `output_all_timeline_keywords` `social_monitor/social_monitor/mcp_client_main.py:68-83,84-106`。
- 常规监控入口：`get_keywords` 支持缓存复用与落库 `social_monitor/social_monitor/mcp_client_main.py:17-48`。
- 核心生成：调用 `BaseSearch.search_timeline_keywords` 产出关键词并清洗 `social_monitor/social_monitor/mcp_client.py:73-112`。

## 一键导出（推荐）
- 直接调用函数：
  - `from social_monitor.media_crawler.social_monitor.mcp_client_main import export_all_plan_keywords_to_file`
  - `await export_all_plan_keywords_to_file('all_plan_keywords.json', time_range='最近三个月', nums=15, progress=True)`
- 终端示例（无需写代码）：
  - `python -c "import asyncio; from social_monitor.media_crawler.social_monitor.mcp_client_main import export_all_plan_keywords_to_file; asyncio.run(export_all_plan_keywords_to_file('all_plan_keywords.json', time_range='最近三个月', nums=15, progress=True))"`

### 流程线
- [选择方案] → [逐个方案生成] → [解析 JSON `timeline_keywords`] → [清洗与规整] → [打印/写文件或入库]

## LLM 提示词策略
- 入口：`BaseSearch.search_timeline_keywords` `social_monitor/social_monitor/mcp_client.py:73-112`。
- 输入：
  - `检测方案名称: {monitor_name}` 来自 `MonitorPlanEntity.plan_name`。
  - `检测方案关键词: {keywords}` 来自 `MonitorPlanEntity.keywords`。
  - `时间要求: {time}` 例如“最近三个月”。
  - `关键词数量要求: {nums}` 控制期望返回条数。
- 约束与输出：
  - 识别“具体事件”，按时间从早到晚排列 `social_monitor/social_monitor/mcp_client.py:81-83`。
  - 短语为“主要人物 标志性事件（必要时机构名）”，仅用空格分隔，无符号连接 `social_monitor/social_monitor/mcp_client.py:84-85`。
  - 禁止具体日期格式（如“2025年11月”“11/04”）与站点名 `social_monitor/social_monitor/mcp_client.py:86-89`。
  - 仅返回 JSON 字段 `timeline_keywords`，便于解析 `social_monitor/social_monitor/mcp_client.py:90-95`。

## 关键词清洗规则
- 清洗函数：`_clean_timeline_keyword` `social_monitor/social_monitor/mcp_client.py:26-41`。
- 动作：
  - 去除各类日期表达（年月日、`YYYY/MM/DD`、`YYYY-MM-DD`、`YYYY M D` 等）。
  - 去除社媒/媒体站点名（微博、抖音、知乎、Bilibili、Twitter、YouTube 等）。
  - 规范空白为单个空格并 `strip()`。
  - 空字符串过滤掉 `social_monitor/social_monitor/mcp_client.py:106-112`。

## 搜索器实现
- `KIMISearch`：Moonshot `$web_search` 工具循环，自动将工具返回加入上下文，直至生成文本 `social_monitor/social_monitor/mcp_client.py:178-205`。
- `BAIDUSearch`：兼容 Chat Completions 接口，直接返回文本 `social_monitor/social_monitor/mcp_client.py:124-131`。

## 存储与复用策略（监控路径）
- 缓存复用：在监控时间间隔内（`monitor_time_interval`）优先复用历史关键词，减少重复搜索 `social_monitor/social_monitor/mcp_client_main.py:25-35`。
- 新生成关键词入库：以 `config.KEYWORD_SEPARATOR` 连接写入 `SearchKeywordsDB` 并记录插入 `id` `social_monitor/social_monitor/mcp_client_main.py:42-48`。

## CLI 参数与使用
- `--output_only true|false`：仅输出模式（不进入循环监控）。
- `--limit N`：前 N 个方案；`N<=0` 时处理全部方案 `social_monitor/social_monitor/mcp_client_main.py:107-137`。
- `--num_keywords K`：期望的时间线关键词数量。
- `--output_file PATH`：写入指定 JSON 文件（否则打印到控制台）。
- `--progress true|false`：显示进度（优先使用 `tqdm`，否则回退行式提示）。
- `--save_data_option db|json|csv`：
  - `db`：初始化数据库连接，稳定读取方案与可落库。
  - `json`：不主动初始化，但在需要时兜底初始化以读取方案列表。

### 示例命令
- 全量导出到文件并显示进度：
  - `python social_monitor/media_crawler/social_monitor/mcp_client_main.py --save_data_option db --output_only true --limit 0 --num_keywords 15 --output_file all_plan_keywords.json --progress true`

## 失败与回退
- 数据库未初始化导致 `ContextVar LookupError`：在仅输出路径兜底动态初始化 DB 后重试 `social_monitor/social_monitor/mcp_client_main.py:68-75,107-137`。
- 空结果回退：若某方案生成的列表为空，退回使用 `plan_name` 作为唯一关键词 `social_monitor/social_monitor/mcp_client_main.py:76-78`。

## 输出格式
- 统一返回结构：`{"data": [{"plan_id": int, "plan_name": str, "keywords": [str, ...]}, ...]}`。
