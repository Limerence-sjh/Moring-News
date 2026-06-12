"""Tests for Server酱 pusher."""

import pytest
from unittest.mock import patch, MagicMock
from morning_news.models import Message
from morning_news.pusher.serverchan import ServerChanPusher


class TestServerChanPusherInit:

    def test_pusher_init_with_config(self):
        """Test pusher initialization with valid config."""
        config = {
            "sendkey": "test-sendkey-123",
            "daily_limit": 5
        }
        pusher = ServerChanPusher(config)
        assert pusher.sendkey == "test-sendkey-123"
        assert pusher.daily_limit == 5

    def test_pusher_default_daily_limit(self):
        """Test pusher defaults daily_limit to 5."""
        config = {"sendkey": "test-key"}
        pusher = ServerChanPusher(config)
        assert pusher.daily_limit == 5


class TestServerChanPush:

    @patch("morning_news.pusher.serverchan.requests.post")
    def test_successful_push_returns_true(self, mock_post):
        """Test that a successful Server酱 push returns True."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"code": 0, "msg": "success"}
        mock_post.return_value = mock_response

        config = {"sendkey": "valid-key"}
        pusher = ServerChanPusher(config)
        msg = Message(title="测试标题", content="测试内容", level="urgent", source="test")
        result = pusher.push(msg)

        assert result is True
        call_args = mock_post.call_args
        assert "valid-key" in call_args[0][0]

    @patch("morning_news.pusher.serverchan.requests.post")
    def test_push_with_invalid_sendkey_returns_false(self, mock_post):
        """Test that push with invalid sendkey returns False."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"code": 40001, "msg": "invalid sendkey"}
        mock_post.return_value = mock_response

        config = {"sendkey": "invalid-key"}
        pusher = ServerChanPusher(config)
        msg = Message(title="测试", content="内容", level="urgent", source="test")
        result = pusher.push(msg)

        assert result is False

    @patch("morning_news.pusher.serverchan.requests.post")
    def test_push_handles_network_error(self, mock_post):
        """Test that push handles network errors gracefully and returns False."""
        mock_post.side_effect = Exception("Network timeout")

        config = {"sendkey": "any-key"}
        pusher = ServerChanPusher(config)
        msg = Message(title="测试", content="内容", level="urgent", source="test")
        result = pusher.push(msg)

        assert result is False

    @patch("morning_news.pusher.serverchan.requests.post")
    def test_push_handles_http_error_status(self, mock_post):
        """Test that push handles HTTP error status codes gracefully."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"code": -1, "msg": "server error"}
        mock_post.return_value = mock_response

        config = {"sendkey": "test-key"}
        pusher = ServerChanPusher(config)
        msg = Message(title="测试", content="内容", level="urgent", source="test")
        result = pusher.push(msg)

        assert result is False

    @patch("morning_news.pusher.serverchan.requests.post")
    def test_push_formats_markdown_content(self, mock_post):
        """Test that push sends content in markdown format."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"code": 0, "msg": "success"}
        mock_post.return_value = mock_response

        config = {"sendkey": "test-key"}
        pusher = ServerChanPusher(config)
        msg = Message(title="标题", content="# Markdown内容\n\n- 列表1\n- 列表2", level="daily", source="test")
        result = pusher.push(msg)

        assert result is True
        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["json"]["desp"] == "# Markdown内容\n\n- 列表1\n- 列表2"

    @patch("morning_news.pusher.serverchan.requests.post")
    def test_push_empty_sendkey_returns_false(self, mock_post):
        """Test that push with empty sendkey returns False without making API call."""
        config = {"sendkey": ""}
        pusher = ServerChanPusher(config)
        msg = Message(title="测试", content="内容", level="urgent", source="test")
        result = pusher.push(msg)

        assert result is False
        mock_post.assert_not_called()