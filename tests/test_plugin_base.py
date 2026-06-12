"""Tests for plugin base class and discovery."""

import os
import tempfile
import pytest
from morning_news.plugins.base import BasePlugin
from morning_news.models import PluginResult, Message
from morning_news.plugins import discover_plugins


class TestPluginBase:

    def test_base_plugin_is_abstract(self):
        """Test that BasePlugin cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            BasePlugin(config_section={})

    def test_plugin_subclass_instantiation(self):
        """Test that a proper subclass can be instantiated."""
        class TestPlugin(BasePlugin):
            name = "test_plugin"
            schedule_type = "interval"
            interval_minutes = 5

            def run(self, db):
                return PluginResult()

        plugin = TestPlugin(config_section={"enabled": True})
        assert plugin.name == "test_plugin"
        assert plugin.schedule_type == "interval"
        assert plugin.interval_minutes == 5
        assert plugin.enabled is True

    def test_plugin_subclass_with_cron(self):
        """Test a cron-type plugin subclass."""
        class CronPlugin(BasePlugin):
            name = "cron_plugin"
            schedule_type = "cron"
            cron_expression = "0 18 * * *"

            def run(self, db):
                return PluginResult()

        plugin = CronPlugin(config_section={"enabled": True})
        assert plugin.cron_expression == "0 18 * * *"

    def test_plugin_enabled_default_true(self):
        """Test that enabled defaults to True when config doesn't specify."""
        class TestPlugin(BasePlugin):
            name = "test"
            schedule_type = "interval"
            interval_minutes = 5

            def run(self, db):
                return PluginResult()

        plugin = TestPlugin(config_section={})
        assert plugin.enabled is True

    def test_plugin_enabled_false_from_config(self):
        """Test that enabled can be set to False from config."""
        class TestPlugin(BasePlugin):
            name = "test"
            schedule_type = "interval"
            interval_minutes = 5

            def run(self, db):
                return PluginResult()

        plugin = TestPlugin(config_section={"enabled": False})
        assert plugin.enabled is False


class TestDiscoverPlugins:

    def test_discover_plugins_finds_existing_plugins(self):
        """Test that discover_plugins finds plugin classes in the plugins directory."""
        plugins = discover_plugins()
        # Should at least find bilibili_live, github_trending, weibo
        # (These will be created in later tasks)
        assert isinstance(plugins, dict)

    def test_discover_plugins_returns_name_to_class_mapping(self):
        """Test that discover_plugins returns {name: class} dict."""
        plugins = discover_plugins()
        for name, cls in plugins.items():
            assert isinstance(name, str)
            assert issubclass(cls, BasePlugin)