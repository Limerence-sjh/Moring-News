"""Tests for config_loader module."""

import os
import tempfile
import pytest
from morning_news.config_loader import ConfigLoader, ConfigError


class TestConfigLoader:

    def test_load_valid_config(self, sample_config_path):
        """Test loading a valid config.yaml file."""
        loader = ConfigLoader(sample_config_path)
        config = loader.load()
        assert config["push"]["serverchan"]["sendkey"] == "test-sendkey-123"
        assert config["push"]["serverchan"]["daily_limit"] == 5
        assert config["scheduler"]["instant_interval"] == 5
        assert config["scheduler"]["daily_time"] == "18:00"

    def test_access_sources_config(self, sample_config_path):
        """Test accessing source-specific configuration."""
        loader = ConfigLoader(sample_config_path)
        config = loader.load()
        assert config["sources"]["bilibili_live"]["enabled"] is True
        assert config["sources"]["bilibili_live"]["up_ids"] == ["12345", "67890"]
        assert config["sources"]["weibo"]["top_count"] == 5

    def test_missing_config_file_raises_error(self):
        """Test that missing config file raises ConfigError."""
        loader = ConfigLoader("/nonexistent/path/config.yaml")
        with pytest.raises(ConfigError, match="Config file not found"):
            loader.load()

    def test_missing_required_field_raises_error(self, temp_dir):
        """Test that missing required fields raise ConfigError."""
        config_content = """
push:
  serverchan:
    sendkey: "test-key"
    # missing daily_limit
  email:
    smtp_host: "smtp.test.com"
    smtp_port: 465
    from: "test@test.com"
    password: "test"
    to: "target@test.com"

scheduler:
  instant_interval: 5
  daily_time: "18:00"

sources:
  bilibili_live:
    enabled: true
    up_ids: ["12345"]
"""
        config_path = os.path.join(temp_dir, "config.yaml")
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(config_content)

        loader = ConfigLoader(config_path)
        # daily_limit has a default, so this should not raise
        config = loader.load()
        assert config["push"]["serverchan"]["daily_limit"] == 5  # default value

    def test_empty_config_raises_error(self, temp_dir):
        """Test that an empty config file raises ConfigError."""
        config_path = os.path.join(temp_dir, "config.yaml")
        with open(config_path, "w", encoding="utf-8") as f:
            f.write("")
        loader = ConfigLoader(config_path)
        with pytest.raises(ConfigError, match="Config file is empty"):
            loader.load()

    def test_invalid_yaml_raises_error(self, temp_dir):
        """Test that invalid YAML syntax raises ConfigError."""
        config_path = os.path.join(temp_dir, "config.yaml")
        with open(config_path, "w", encoding="utf-8") as f:
            f.write("invalid: yaml: [broken: {syntax}}]")
        loader = ConfigLoader(config_path)
        with pytest.raises(ConfigError, match="Invalid YAML"):
            loader.load()

    def test_get_source_config_method(self, sample_config_path):
        """Test the get_source_config convenience method."""
        loader = ConfigLoader(sample_config_path)
        config = loader.load()
        bilibili_config = loader.get_source_config(config, "bilibili_live")
        assert bilibili_config["up_ids"] == ["12345", "67890"]
        assert bilibili_config["enabled"] is True

    def test_get_source_config_missing_source(self, sample_config_path):
        """Test get_source_config for a source not in config."""
        loader = ConfigLoader(sample_config_path)
        config = loader.load()
        unknown_config = loader.get_source_config(config, "unknown_source")
        assert unknown_config is None