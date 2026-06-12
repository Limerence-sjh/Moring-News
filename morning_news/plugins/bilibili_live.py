"""B站UP主开播通知 + 标题采集插件.

Monitors B站UP主直播状态 every 5 minutes:
- When UP主 transitions from offline to live → push urgent notification
- Every check: save current title to database for daily summary
"""

import requests
from typing import Dict, Optional
from morning_news.plugins.base import BasePlugin
from morning_news.models import Message, PluginResult


BILIBILI_LIVE_API = "https://api.live.bilibili.com/room/v1/Room/get_status_info_by_uids"


class BilibiliLivePlugin(BasePlugin):
    """Monitor B站UP主 live stream status and push notifications on开播.

    Config keys:
        up_ids: List of UP主 UID strings to monitor.
    """

    name = "bilibili_live"
    schedule_type = "interval"
    interval_minutes = 5

    def __init__(self, config_section: dict):
        """Initialize with UP主 IDs from config.

        Args:
            config_section: Dict with 'up_ids' list and optional 'enabled' flag.
        """
        super().__init__(config_section)
        self.up_ids = config_section.get("up_ids", [])

    def run(self, db) -> PluginResult:
        """Check live status for all monitored UP主s.

        For each UP主:
        1. Fetch current live status from B站 API
        2. Compare with last known status from database
        3. If transition from offline→live: create urgent Message
        4. Always save current title and status to database

        Args:
            db: Database instance for state persistence.

        Returns:
            PluginResult with urgent messages (if any) and current status data.
        """
        messages = []

        if not self.up_ids:
            return PluginResult(messages=[], data={})

        # Fetch all UP主s' status in one API call
        live_data = self._fetch_live_status()
        if live_data is None:
            return PluginResult(messages=[], data={"error": "api_fetch_failed"})

        for up_id in self.up_ids:
            up_data = live_data.get(str(up_id))
            if up_data is None:
                continue

            is_live = up_data.get("live_status", 0) in (1, 2)
            title = up_data.get("title", "")
            uname = up_data.get("uname", up_id)

            # Save UP主 name for better notifications
            db.save_up_name(up_id=up_id, name=uname)

            # Check if this is a transition from offline to live
            last_status = db.get_last_live_status(up_id=up_id)
            was_live = last_status["is_live"]

            if not was_live and is_live:
                messages.append(Message(
                    title=f"🔴 {uname} 开播了",
                    content=f"直播间标题: {title}",
                    level="urgent",
                    source=self.name
                ))

            # Always save current status and title to database
            db.save_live_record(up_id=up_id, title=title, is_live=is_live)

        return PluginResult(messages=messages, data={"checked_ups": self.up_ids})

    def _fetch_live_status(self) -> Optional[Dict]:
        """Fetch live status for all monitored UP主s from B站 API.

        Makes a single POST request with all UP IDs.

        Returns:
            Dict of {uid: status_data} from API, or None on error.
        """
        try:
            payload = {"uids": [int(uid) for uid in self.up_ids]}
            response = requests.post(
                BILIBILI_LIVE_API,
                json=payload,
                timeout=10
            )
            if response.status_code != 200:
                return None

            result = response.json()
            if result.get("code") != 0:
                return None

            return result.get("data", {})
        except Exception:
            return None