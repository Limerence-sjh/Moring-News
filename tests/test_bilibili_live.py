"""Tests for B站UP主开播 plugin."""

import json
import pytest
from unittest.mock import patch, MagicMock
from morning_news.plugins.bilibili_live import BilibiliLivePlugin
from morning_news.models import PluginResult


class TestBilibiliLivePluginInit:

    def test_plugin_init_with_config(self):
        """Test plugin initialization reads UP IDs from config."""
        config = {
            "enabled": True,
            "up_ids": ["12345", "67890"]
        }
        plugin = BilibiliLivePlugin(config_section=config)
        assert plugin.name == "bilibili_live"
        assert plugin.schedule_type == "interval"
        assert plugin.interval_minutes == 5
        assert plugin.up_ids == ["12345", "67890"]

    def test_plugin_enabled_from_config(self):
        """Test plugin enabled/disabled from config."""
        plugin_enabled = BilibiliLivePlugin(config_section={"enabled": True, "up_ids": ["1"]})
        plugin_disabled = BilibiliLivePlugin(config_section={"enabled": False, "up_ids": ["1"]})
        assert plugin_enabled.enabled is True
        assert plugin_disabled.enabled is False


class TestBilibiliLivePluginRun:

    def _mock_api_response(self, up_id, live_status, title=""):
        """Create a mock B站 API response for a single UP主.

        Args:
            up_id: UP主 UID.
            live_status: 0=offline, 1=live, 2=streaming.
            title: Live room title.
        """
        return {
            "code": 0,
            "msg": "success",
            "data": {
                str(up_id): {
                    "live_status": live_status,
                    "title": title,
                    "room_id": 12345,
                    "uname": f"UP主_{up_id}"
                }
            }
        }

    @patch("morning_news.plugins.bilibili_live.requests.post")
    def test_detect_live_transition_generates_urgent_message(self, mock_post, db):
        """Test that transition from offline to live generates an urgent message."""
        # UP主 was offline before (db has no records)
        # Now API returns live status
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self._mock_api_response("12345", 1, "连麦答疑")
        mock_post.return_value = mock_response

        config = {"enabled": True, "up_ids": ["12345"]}
        plugin = BilibiliLivePlugin(config_section=config)
        result = plugin.run(db)

        assert result.has_messages is True
        assert result.messages[0].level == "urgent"
        assert "开播了" in result.messages[0].title
        assert "连麦答疑" in result.messages[0].content

    @patch("morning_news.plugins.bilibili_live.requests.post")
    def test_no_message_when_already_online(self, mock_post, db):
        """Test no urgent message when UP主 was already live (no state change)."""
        # First run: UP主 goes online
        mock_response1 = MagicMock()
        mock_response1.status_code = 200
        mock_response1.json.return_value = self._mock_api_response("12345", 1, "聊天")
        mock_post.return_value = mock_response1

        config = {"enabled": True, "up_ids": ["12345"]}
        plugin = BilibiliLivePlugin(config_section=config)
        result1 = plugin.run(db)

        # Second run: UP主 still online, same status
        mock_response2 = MagicMock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = self._mock_api_response("12345", 1, "聊天")
        mock_post.return_value = mock_response2

        result2 = plugin.run(db)
        assert not result2.has_messages  # No new messages since status unchanged

    @patch("morning_news.plugins.bilibili_live.requests.post")
    def test_title_always_saved_to_db(self, mock_post, db):
        """Test that title is saved to DB even when no message is generated."""
        # UP主 was online before, still online now (no transition)
        db.save_live_record(up_id="12345", title="旧标题", is_live=True)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self._mock_api_response("12345", 1, "新标题")
        mock_post.return_value = mock_response

        config = {"enabled": True, "up_ids": ["12345"]}
        plugin = BilibiliLivePlugin(config_section=config)
        result = plugin.run(db)

        # No message (status unchanged), but title should be saved
        assert not result.has_messages
        last_status = db.get_last_live_status("12345")
        assert last_status["title"] == "新标题"

    @patch("morning_news.plugins.bilibili_live.requests.post")
    def test_multiple_up_ids(self, mock_post, db):
        """Test handling multiple UP IDs with different statuses."""
        api_data = {
            "code": 0,
            "msg": "success",
            "data": {
                "11111": {"live_status": 1, "title": "直播中", "room_id": 111, "uname": "UP_A"},
                "22222": {"live_status": 0, "title": "", "room_id": 222, "uname": "UP_B"},
            }
        }
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = api_data
        mock_post.return_value = mock_response

        config = {"enabled": True, "up_ids": ["11111", "22222"]}
        plugin = BilibiliLivePlugin(config_section=config)
        result = plugin.run(db)

        # Only UP_A (transition from offline to live) should generate a message
        assert result.has_messages is True
        urgent_msgs = [m for m in result.messages if m.level == "urgent"]
        assert len(urgent_msgs) == 1
        assert "UP_A" in urgent_msgs[0].title or "11111" in urgent_msgs[0].title

    @patch("morning_news.plugins.bilibili_live.requests.post")
    def test_api_error_returns_empty_messages(self, mock_post, db):
        """Test that API errors don't crash the plugin and return empty messages."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"code": -1, "msg": "error"}
        mock_post.return_value = mock_response

        config = {"enabled": True, "up_ids": ["12345"]}
        plugin = BilibiliLivePlugin(config_section=config)
        result = plugin.run(db)

        assert not result.has_messages  # No messages on API error

    @patch("morning_news.plugins.bilibili_live.requests.post")
    def test_network_error_returns_empty_messages(self, mock_post, db):
        """Test that network errors are handled gracefully."""
        mock_post.side_effect = Exception("Network error")

        config = {"enabled": True, "up_ids": ["12345"]}
        plugin = BilibiliLivePlugin(config_section=config)
        result = plugin.run(db)

        assert not result.has_messages  # No messages on network error