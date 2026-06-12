"""Push manager for Morning News - handles priority routing and fallback.

Strategy:
- urgent messages: always try Server酱 first, fallback to email
- daily messages: check Server酱 daily limit first; if limit reached, go straight to email
- All push attempts are logged to the database
"""

from dataclasses import dataclass
from typing import Optional
from morning_news.models import Message
from morning_news.pusher.serverchan import ServerChanPusher
from morning_news.pusher.email import EmailPusher


@dataclass
class PushResult:
    """Result of a push attempt.

    Args:
        channel: Which channel was used ('serverchan' or 'email').
        success: Whether the push succeeded.
        message_title: Title of the pushed message.
    """

    channel: str
    success: bool
    message_title: str = ""


class PushManager:
    """Orchestrate message pushing with priority and fallback logic.

    Args:
        serverchan_config: Config dict for Server酱 pusher.
        email_config: Config dict for email pusher.
        db: Database instance for push logging and limit checking.
    """

    def __init__(self, serverchan_config: dict, email_config: dict, db):
        self.serverchan = ServerChanPusher(serverchan_config)
        self.email = EmailPusher(email_config)
        self.db = db

    def push(self, message: Message) -> PushResult:
        """Push a message using the appropriate channel based on priority.

        For urgent messages:
        1. Try Server酱 (ignores daily limit)
        2. If Server酱 fails, fallback to email

        For daily messages:
        1. Check Server酱 daily limit
        2. If limit not reached, try Server酱
        3. If limit reached or Server酱 fails, try email

        Args:
            message: Message to push.

        Returns:
            PushResult indicating which channel was used and whether it succeeded.
        """
        if message.level == "urgent":
            return self._push_urgent(message)
        else:
            return self._push_daily(message)

    def _push_urgent(self, message: Message) -> PushResult:
        success = self.serverchan.push(message)
        self.db.save_push_log(
            channel="serverchan",
            level=message.level,
            source=message.source,
            title=message.title,
            content=message.content,
            success=success
        )

        if success:
            return PushResult(channel="serverchan", success=True, message_title=message.title)

        success = self.email.push(message)
        self.db.save_push_log(
            channel="email",
            level=message.level,
            source=message.source,
            title=message.title,
            content=message.content,
            success=success
        )

        if success:
            return PushResult(channel="email", success=True, message_title=message.title)

        return PushResult(channel="none", success=False, message_title=message.title)

    def _push_daily(self, message: Message) -> PushResult:
        push_count = self.db.get_push_count_today(channel="serverchan")

        if push_count >= self.serverchan.daily_limit:
            success = self.email.push(message)
            self.db.save_push_log(
                channel="email",
                level=message.level,
                source=message.source,
                title=message.title,
                content=message.content,
                success=success
            )
            if success:
                return PushResult(channel="email", success=True, message_title=message.title)
            return PushResult(channel="none", success=False, message_title=message.title)

        success = self.serverchan.push(message)
        self.db.save_push_log(
            channel="serverchan",
            level=message.level,
            source=message.source,
            title=message.title,
            content=message.content,
            success=success
        )

        if success:
            return PushResult(channel="serverchan", success=True, message_title=message.title)

        success = self.email.push(message)
        self.db.save_push_log(
            channel="email",
            level=message.level,
            source=message.source,
            title=message.title,
            content=message.content,
            success=success
        )

        if success:
            return PushResult(channel="email", success=True, message_title=message.title)

        return PushResult(channel="none", success=False, message_title=message.title)