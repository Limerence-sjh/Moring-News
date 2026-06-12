"""微博热搜 plugin for Morning News.

Fetches Weibo hot search list from the Weibo API
and formats them as a daily summary message.
"""

import requests
from datetime import date
from typing import Dict, List, Optional
from morning_news.plugins.base import BasePlugin
from morning_news.models import Message, PluginResult


WEIBO_HOT_SEARCH_API = "https://weibo.com/ajax/side/hotSearch"


class WeiboPlugin(BasePlugin):
    """Fetch Weibo hot search items and format as daily summary.

    Config keys:
        top_count: Number of top items to include (default 5).
    """

    name = "weibo"
    schedule_type = "cron"
    cron_expression = "0 18 * * *"

    def __init__(self, config_section: dict):
        super().__init__(config_section)
        self.top_count = config_section.get("top_count", 5)

    def run(self, db) -> PluginResult:
        data = self._fetch_hot_search()
        if data is None:
            return PluginResult(messages=[], data={"error": "fetch_failed"})

        items = self._parse_items(data)
        items = items[:self.top_count]

        if not items:
            return PluginResult(messages=[], data={"items": []})

        today = date.today().isoformat()
        db.save_daily_data(source=self.name, date=today, data={"items": items})

        content = self._format_message(items)
        message = Message(
            title="微博热搜",
            content=content,
            level="daily",
            source=self.name
        )

        return PluginResult(messages=[message], data={"items": items})

    def _fetch_hot_search(self) -> Optional[Dict]:
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = requests.get(
                WEIBO_HOT_SEARCH_API,
                headers=headers,
                timeout=10
            )
            if response.status_code != 200:
                return None
            return response.json()
        except Exception:
            return None

    def _parse_items(self, data: Dict) -> List[Dict]:
        realtime = data.get("data", {}).get("realtime", [])
        if not realtime:
            return []

        items = []
        for entry in realtime:
            word = entry.get("word", "")
            category = entry.get("category", "") or ""
            num = entry.get("num", 0)
            rank = entry.get("rank", 0)

            items.append({
                "word": word,
                "category": category,
                "num": num,
                "rank": rank,
            })

        items.sort(key=lambda x: x["rank"])
        return items

    def _format_message(self, items: List[Dict]) -> str:
        lines = []
        for i, item in enumerate(items, 1):
            parts = [f"{i}. {item['word']}"]
            if item["category"]:
                parts.append(f"[{item['category']}]")
            lines.append(" ".join(parts))
        return "\n".join(lines)