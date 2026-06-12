"""Base plugin class for Morning News.

All info source plugins must inherit from BasePlugin and implement the run() method.
"""

from abc import ABC, abstractmethod
from morning_news.models import PluginResult


class BasePlugin(ABC):
    """Abstract base class for Morning News plugins.

    Every plugin must define:
    - name: Unique string identifier
    - schedule_type: 'interval' (periodic polling) or 'cron' (scheduled time)
    - run(): Method that executes data collection and returns results

    Args:
        config_section: Dict of plugin-specific configuration from config.yaml.
    """

    name: str = ""
    schedule_type: str = "interval"  # "interval" or "cron"
    interval_minutes: int = 5        # For interval-type plugins
    cron_expression: str = ""        # For cron-type plugins

    def __init__(self, config_section: dict):
        """Initialize plugin with its configuration section.

        Args:
            config_section: Plugin-specific config dict from config.yaml sources section.
        """
        self.enabled = config_section.get("enabled", True)
        self._config = config_section

    @abstractmethod
    def run(self, db) -> PluginResult:
        """Execute one data collection cycle.

        Args:
            db: Database instance for reading/writing state and history.

        Returns:
            PluginResult containing messages to push and data to persist.
        """
        ...