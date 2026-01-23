import os
import json
import time
from typing import Dict


class KeywordProgressCache:
    """
    关键词进度文件缓存：记录某个方案(plan_id)下已完成的关键词，避免中断后重复爬取。

    数据结构示例：
    {
        "123": {
            "鸡排哥最近咋样了": {"completed": true, "ts": 1731500000000},
            "另一个关键词": {"completed": true, "ts": 1731500010000}
        },
        "456": { ... }
    }
    """

    def __init__(self, cache_file: str = "social_monitor/cache/keyword_progress.json") -> None:
        self.cache_file = cache_file
        self._cache: Dict[str, Dict[str, Dict]] = {}
        self._ensure_dir()
        self._load()

    def _ensure_dir(self) -> None:
        d = os.path.dirname(self.cache_file)
        if d and not os.path.exists(d):
            os.makedirs(d, exist_ok=True)

    def _load(self) -> None:
        if not os.path.exists(self.cache_file):
            self._cache = {}
            return
        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                self._cache = json.load(f)
                if not isinstance(self._cache, dict):
                    self._cache = {}
        except Exception:
            # 文件损坏或内容异常时，回退为空
            self._cache = {}

    def _save(self) -> None:
        tmp_path = self.cache_file + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(self._cache, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, self.cache_file)

    def is_done(self, plan_id: int, keyword: str) -> bool:
        pid = str(plan_id)
        kw = keyword.strip()
        return bool(self._cache.get(pid, {}).get(kw, {}).get("completed", False))

    def mark_done(self, plan_id: int, keyword: str) -> None:
        pid = str(plan_id)
        kw = keyword.strip()
        if pid not in self._cache:
            self._cache[pid] = {}
        self._cache[pid][kw] = {"completed": True, "ts": int(time.time() * 1000)}
        self._save()