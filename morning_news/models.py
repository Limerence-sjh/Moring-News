"""Data models for Morning News.

Defines Message (for push notifications) and PluginResult (for plugin output).
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional


VALID_LEVELS = ("urgent", "daily")


@dataclass
class Message:
    """A push notification message.

    Args:
        title: Message headline (shown in push notification).
        content: Message body text (may include Markdown).
        level: Priority level - 'urgent' for instant alerts, 'daily' for summaries.
        source: Name of the plugin that generated this message.
    """

    title: str
    content: str
    level: str = "daily"
    source: str = ""

    def __post_init__(self):
        """Validate level after initialization."""
        if self.level not in VALID_LEVELS:
            raise ValueError(
                f"Invalid level '{self.level}'. Must be one of: {VALID_LEVELS}"
            )

    def to_dict(self) -> Dict:
        """Serialize Message to dictionary.

        Returns:
            Dict representation of the message.
        """
        return {
            "title": self.title,
            "content": self.content,
            "level": self.level,
            "source": self.source,
        }


@dataclass
class PluginResult:
    """Output from a plugin run.

    Args:
        messages: List of Message objects to be pushed immediately.
        data: Arbitrary dict of data to persist in database (for daily summary).
    """

    messages: List[Message] = field(default_factory=list)
    data: Dict = field(default_factory=dict)

    @property
    def has_messages(self) -> bool:
        """Check if this result contains any messages to push.

        Returns:
            True if there are messages, False otherwise.
        """
        return len(self.messages) > 0