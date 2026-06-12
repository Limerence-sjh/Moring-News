"""Tests for 微博 hot search plugin."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import date
from morning_news.plugins.weibo import WeiboPlugin
from morning_news.models import PluginResult


MOCK_WEIBO_DATA = {
    "data": {
        "realtime": [
            {"word": "热搜话题A", "category": "社会", "num": 100000, "rank": 1},
            {"word": "热搜话题B", "category": "娱乐", "num": 80000, "rank": 2},
            {"word": "热搜话题C", "category": "科技", "num": 50000, "rank": 3},
            {"word": "热搜话题D", "category": "", "num": 30000, "rank": 4},
            {"word": "热搜话题E", "category": "财经", "num": 25000, "rank": 5},
            {"word": "热搜话题F", "category": "体育", "num": 20000, "rank": 6},
            {"word": "热搜话题G", "category": "教育", "num": 15000, "rank": 7},
        ]
    }
}


class TestWeiboPluginInit:

    def test_plugin_init_defaults(self):
        config = {"enabled": True}
        plugin = WeiboPlugin(config_section=config)
        assert plugin.name == "weibo"
        assert plugin.schedule_type == "cron"
        assert plugin.cron_expression == "0 18 * * *"
        assert plugin.top_count == 5

    def test_plugin_init_with_config(self):
        config = {"enabled": True, "top_count": 3}
        plugin = WeiboPlugin(config_section=config)
        assert plugin.top_count == 3

    def test_plugin_enabled_from_config(self):
        plugin_enabled = WeiboPlugin(config_section={"enabled": True})
        plugin_disabled = WeiboPlugin(config_section={"enabled": False})
        assert plugin_enabled.enabled is True
        assert plugin_disabled.enabled is False


class TestWeiboPluginRun:

    @patch("morning_news.plugins.weibo.requests.get")
    def test_run_returns_daily_message(self, mock_get, db):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_WEIBO_DATA
        mock_get.return_value = mock_response

        plugin = WeiboPlugin(config_section={"enabled": True, "top_count": 5})
        result = plugin.run(db)

        assert result.has_messages is True
        assert result.messages[0].level == "daily"
        assert result.messages[0].title == "微博热搜"
        assert result.messages[0].source == "weibo"

    @patch("morning_news.plugins.weibo.requests.get")
    def test_top_count_limits_items(self, mock_get, db):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_WEIBO_DATA
        mock_get.return_value = mock_response

        plugin = WeiboPlugin(config_section={"enabled": True, "top_count": 3})
        result = plugin.run(db)

        items = result.data["items"]
        assert len(items) == 3
        assert items[0]["word"] == "热搜话题A"
        assert items[1]["word"] == "热搜话题B"
        assert items[2]["word"] == "热搜话题C"

    @patch("morning_news.plugins.weibo.requests.get")
    def test_item_parsing(self, mock_get, db):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_WEIBO_DATA
        mock_get.return_value = mock_response

        plugin = WeiboPlugin(config_section={"enabled": True, "top_count": 7})
        result = plugin.run(db)

        items = result.data["items"]
        assert items[0]["category"] == "社会"
        assert items[0]["num"] == 100000
        assert items[0]["rank"] == 1
        assert items[3]["category"] == ""

    @patch("morning_news.plugins.weibo.requests.get")
    def test_message_format(self, mock_get, db):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_WEIBO_DATA
        mock_get.return_value = mock_response

        plugin = WeiboPlugin(config_section={"enabled": True, "top_count": 4})
        result = plugin.run(db)

        content = result.messages[0].content
        lines = content.strip().split("\n")
        assert len(lines) == 4
        assert lines[0].startswith("1.")
        assert "热搜话题A" in lines[0]
        assert "[社会]" in lines[0]
        assert lines[3].startswith("4.")
        assert "热搜话题D" in lines[3]

    @patch("morning_news.plugins.weibo.requests.get")
    def test_message_format_no_category(self, mock_get, db):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_WEIBO_DATA
        mock_get.return_value = mock_response

        plugin = WeiboPlugin(config_section={"enabled": True, "top_count": 4})
        result = plugin.run(db)

        content = result.messages[0].content
        lines = content.strip().split("\n")
        assert "热搜话题D" in lines[3]
        assert "[" not in lines[3]

    @patch("morning_news.plugins.weibo.requests.get")
    def test_api_error_returns_empty_result(self, mock_get, db):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.json.return_value = {}
        mock_get.return_value = mock_response

        plugin = WeiboPlugin(config_section={"enabled": True})
        result = plugin.run(db)

        assert not result.has_messages
        assert result.data.get("error") == "fetch_failed"

    @patch("morning_news.plugins.weibo.requests.get")
    def test_network_error_returns_empty_result(self, mock_get, db):
        mock_get.side_effect = Exception("Network error")

        plugin = WeiboPlugin(config_section={"enabled": True})
        result = plugin.run(db)

        assert not result.has_messages

    @patch("morning_news.plugins.weibo.requests.get")
    def test_db_save_called(self, mock_get, db):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_WEIBO_DATA
        mock_get.return_value = mock_response

        plugin = WeiboPlugin(config_section={"enabled": True})
        plugin.run(db)

        saved = db.get_daily_data(source="weibo", date=date.today().isoformat())
        assert saved is not None
        assert "items" in saved

    @patch("morning_news.plugins.weibo.requests.get")
    def test_empty_list_no_message(self, mock_get, db):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"realtime": []}}
        mock_get.return_value = mock_response

        plugin = WeiboPlugin(config_section={"enabled": True})
        result = plugin.run(db)

        assert not result.has_messages
        assert result.data == {"items": []}