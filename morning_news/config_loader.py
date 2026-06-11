"""Configuration loader for Morning News.

Loads and validates config.yaml, providing dict-like access to configuration values.
"""

import os
import yaml


class ConfigError(Exception):
    """Raised when configuration is invalid or missing."""
    pass


class ConfigLoader:
    """Load and validate Morning News configuration from YAML file.

    Args:
        config_path: Path to config.yaml file.

    Raises:
        ConfigError: If file is missing, empty, or contains invalid YAML.
    """

    REQUIRED_TOP_KEYS = ["push", "scheduler", "sources"]
    DEFAULT_VALUES = {
        "push.serverchan.daily_limit": 5,
        "scheduler.instant_interval": 5,
        "scheduler.daily_time": "18:00",
    }

    def __init__(self, config_path: str):
        self.config_path = config_path

    def load(self) -> dict:
        """Load config.yaml and return validated config dict.

        Returns:
            Validated configuration dictionary.

        Raises:
            ConfigError: If file not found, empty, invalid YAML, or missing required keys.
        """
        if not os.path.exists(self.config_path):
            raise ConfigError(f"Config file not found: {self.config_path}")

        with open(self.config_path, "r", encoding="utf-8") as f:
            content = f.read()

        if not content.strip():
            raise ConfigError("Config file is empty")

        try:
            config = yaml.safe_load(content)
        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML: {e}")

        if config is None:
            raise ConfigError("Config file is empty")

        # Validate required top-level keys
        for key in self.REQUIRED_TOP_KEYS:
            if key not in config:
                raise ConfigError(f"Missing required config key: {key}")

        # Apply default values for missing optional fields
        self._apply_defaults(config)

        return config

    def get_source_config(self, config: dict, source_name: str):
        """Get configuration for a specific source.

        Args:
            config: Full config dict.
            source_name: Name of the source (e.g., 'bilibili_live').

        Returns:
            Source config dict, or None if source not found.
        """
        sources = config.get("sources", {})
        return sources.get(source_name)

    def _apply_defaults(self, config: dict) -> None:
        """Apply default values for missing optional configuration fields.

        Args:
            config: Config dict to fill with defaults.
        """
        # Server酱 daily_limit default
        serverchan = config.get("push", {}).get("serverchan", {})
        if "daily_limit" not in serverchan:
            serverchan["daily_limit"] = self.DEFAULT_VALUES["push.serverchan.daily_limit"]

        # Scheduler defaults
        scheduler = config.get("scheduler", {})
        if "instant_interval" not in scheduler:
            scheduler["instant_interval"] = self.DEFAULT_VALUES["scheduler.instant_interval"]
        if "daily_time" not in scheduler:
            scheduler["daily_time"] = self.DEFAULT_VALUES["scheduler.daily_time"]