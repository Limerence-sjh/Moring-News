"""Server酱 pusher for WeChat notifications.

Uses the Server酱 (SCTAPI) HTTP API to push messages to WeChat via official account.
Docs: https://sct.ftqq.com/
"""

import requests
from morning_news.models import Message


SERVERCHAN_API_URL = "https://sctapi.ftqq.com/{sendkey}.send"


class ServerChanPusher:
    """Push notifications to WeChat via Server酱.

    Args:
        config: Dict with 'sendkey' and optional 'daily_limit'.
    """

    def __init__(self, config: dict):
        """Initialize Server酱 pusher with config.

        Args:
            config: Must contain 'sendkey' string. 'daily_limit' defaults to 5.
        """
        self.sendkey = config.get("sendkey", "")
        self.daily_limit = config.get("daily_limit", 5)

    def push(self, message: Message) -> bool:
        """Push a message to WeChat via Server酱.

        Args:
            message: Message to push.

        Returns:
            True if push succeeded, False if push failed or sendkey is empty.
        """
        if not self.sendkey:
            return False

        url = SERVERCHAN_API_URL.format(sendkey=self.sendkey)

        try:
            response = requests.post(
                url,
                json={
                    "title": message.title,
                    "desp": message.content,
                },
                timeout=15
            )

            if response.status_code != 200:
                return False

            result = response.json()
            return result.get("code") == 0

        except Exception:
            return False