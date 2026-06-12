"""Template plugin for Morning News.

Copy this file as a starting point for creating new info source plugins.
Rename the file and the class, then implement the run() method.

Every plugin must:
1. Set name to a unique identifier (used in config.yaml sources section)
2. Set schedule_type to "interval" (periodic) or "cron" (daily summary)
3. Implement run(db) -> PluginResult

See bilibili_live.py for an interval-type plugin example.
See github_trending.py or weibo.py for cron-type plugin examples.
"""

from morning_news.plugins.base import BasePlugin
from morning_news.models import Message, PluginResult


class TemplatePlugin(BasePlugin):
    """Template plugin - copy and customize for your own info source.

    Config keys (define whatever you need):
        url: API endpoint or website to fetch data from.
        keyword: Filter keyword for results.
    """

    name = "template"
    schedule_type = "interval"
    interval_minutes = 5

    def __init__(self, config_section: dict):
        super().__init__(config_section)
        # self.url = config_section.get("url", "")
        # self.keyword = config_section.get("keyword", "")

    def run(self, db) -> PluginResult:
        """Execute one data collection cycle.

        Typical implementation steps:
        1. Fetch data from API or website
        2. Compare with previous state from database (db.get_daily_data, etc.)
        3. Create Message objects for new/changed items
        4. Save data to database for daily summaries (db.save_daily_data, etc.)
        5. Return PluginResult with messages and data

        Example (commented out - adapt for your source):

        # --- Step 1: Fetch data ---
        # try:
        #     response = requests.get(self.url, timeout=10)
        #     data = response.json()
        # except Exception:
        #     logger.exception("Failed to fetch from %s", self.url)
        #     return PluginResult(messages=[], data={"error": "fetch_failed"})

        # --- Step 2: Check state ---
        # today = date.today().isoformat()
        # previous = db.get_daily_data(source=self.name, date=today)
        # if previous is not None:
        #     # Already collected today, skip
        #     return PluginResult(messages=[], data=previous)

        # --- Step 3: Create messages ---
        # messages = []
        # for item in data.get("items", []):
        #     if self.keyword and self.keyword not in item.get("title", "":
        #         continue
        #     messages.append(Message(
        #         title=item["title"],
        #         content=item["description"],
        #         level="daily",        # "urgent" for instant, "daily" for summaries
        #         source=self.name,
        #     ))

        # --- Step 4: Save to DB ---
        # db.save_daily_data(
        #     source=self.name,
        #     date=today,
        #     data={"items": [m.to_dict() for m in messages]},
        # )

        # --- Step 5: Return result ---
        # return PluginResult(messages=messages, data={"count": len(messages)})

        Args:
            db: Database instance for reading/writing state and history.

        Returns:
            PluginResult containing messages to push and data to persist.
        """
        return PluginResult(messages=[], data={})