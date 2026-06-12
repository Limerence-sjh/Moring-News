"""Tests for push manager - priority routing and fallback logic."""

import pytest
from unittest.mock import MagicMock, patch
from morning_news.models import Message
from morning_news.pusher.manager import PushManager, PushResult
from morning_news.pusher.serverchan import ServerChanPusher
from morning_news.pusher.email import EmailPusher


class TestPushResult:

    def test_push_result_creation(self):
        """Test creating a PushResult."""
        result = PushResult(channel="serverchan", success=True, message_title="Test")
        assert result.channel == "serverchan"
        assert result.success is True
        assert result.message_title == "Test"

    def test_push_result_defaults(self):
        """Test PushResult default values."""
        result = PushResult(channel="email", success=False)
        assert result.message_title == ""


class TestPushManagerInit:

    def test_manager_init_with_pushers(self):
        """Test PushManager initialization with both pusher configs."""
        serverchan_config = {"sendkey": "test-key", "daily_limit": 5}
        email_config = {
            "smtp_host": "smtp.test.com",
            "smtp_port": 465,
            "from": "sender@test.com",
            "password": "test-password",
            "to": "receiver@test.com"
        }
        manager = PushManager(serverchan_config=serverchan_config, email_config=email_config, db=MagicMock())
        assert manager.serverchan.sendkey == "test-key"
        assert manager.email.smtp_host == "smtp.test.com"

    def test_manager_init_without_serverchan(self):
        """Test PushManager initialization with empty serverchan config."""
        serverchan_config = {"sendkey": "", "daily_limit": 5}
        email_config = {
            "smtp_host": "smtp.test.com",
            "smtp_port": 465,
            "from": "sender@test.com",
            "password": "test-password",
            "to": "receiver@test.com"
        }
        manager = PushManager(serverchan_config=serverchan_config, email_config=email_config, db=MagicMock())
        assert manager.serverchan.sendkey == ""


class TestPushManagerRouting:

    def test_urgent_message_tries_serverchan_first(self):
        """Test that urgent messages try Server酱 first."""
        mock_db = MagicMock()
        mock_db.get_push_count_today.return_value = 0
        mock_db.save_push_log = MagicMock()

        serverchan_config = {"sendkey": "valid-key", "daily_limit": 5}
        email_config = {
            "smtp_host": "smtp.test.com",
            "smtp_port": 465,
            "from": "sender@test.com",
            "password": "test-password",
            "to": "receiver@test.com"
        }
        manager = PushManager(serverchan_config=serverchan_config, email_config=email_config, db=mock_db)

        msg = Message(title="🔴 UP主开播", content="标题: xxx", level="urgent", source="bilibili_live")

        with patch.object(manager.serverchan, "push", return_value=True) as mock_serverchan:
            result = manager.push(msg)
            mock_serverchan.assert_called_once_with(msg)
            assert result.channel == "serverchan"
            assert result.success is True

    def test_fallback_to_email_when_serverchan_fails(self):
        """Test that push falls back to email when Server酱 fails."""
        mock_db = MagicMock()
        mock_db.get_push_count_today.return_value = 0
        mock_db.save_push_log = MagicMock()

        serverchan_config = {"sendkey": "valid-key", "daily_limit": 5}
        email_config = {
            "smtp_host": "smtp.test.com",
            "smtp_port": 465,
            "from": "sender@test.com",
            "password": "test-password",
            "to": "receiver@test.com"
        }
        manager = PushManager(serverchan_config=serverchan_config, email_config=email_config, db=mock_db)

        msg = Message(title="🔴 UP主开播", content="标题: xxx", level="urgent", source="bilibili_live")

        with patch.object(manager.serverchan, "push", return_value=False):
            with patch.object(manager.email, "push", return_value=True) as mock_email:
                result = manager.push(msg)
                mock_email.assert_called_once_with(msg)
                assert result.channel == "email"
                assert result.success is True

    def test_daily_limit_enforcement_for_daily_messages(self):
        """Test that daily messages check Server酱 daily limit."""
        mock_db = MagicMock()
        mock_db.get_push_count_today.return_value = 4  # Already 4 pushes today
        mock_db.save_push_log = MagicMock()

        serverchan_config = {"sendkey": "valid-key", "daily_limit": 5}
        email_config = {
            "smtp_host": "smtp.test.com",
            "smtp_port": 465,
            "from": "sender@test.com",
            "password": "test-password",
            "to": "receiver@test.com"
        }
        manager = PushManager(serverchan_config=serverchan_config, email_config=email_config, db=mock_db)

        msg = Message(title="📰 每日摘要", content="GitHub Trending...", level="daily", source="github_trending")

        # With 4/5 limit used, one more daily push should still go to serverchan
        with patch.object(manager.serverchan, "push", return_value=True) as mock_serverchan:
            result = manager.push(msg)
            mock_serverchan.assert_called_once_with(msg)
            assert result.channel == "serverchan"

    def test_daily_message_goes_to_email_when_limit_reached(self):
        """Test that daily messages go directly to email when Server酱 limit is reached."""
        mock_db = MagicMock()
        mock_db.get_push_count_today.return_value = 5  # Already at limit
        mock_db.save_push_log = MagicMock()

        serverchan_config = {"sendkey": "valid-key", "daily_limit": 5}
        email_config = {
            "smtp_host": "smtp.test.com",
            "smtp_port": 465,
            "from": "sender@test.com",
            "password": "test-password",
            "to": "receiver@test.com"
        }
        manager = PushManager(serverchan_config=serverchan_config, email_config=email_config, db=mock_db)

        msg = Message(title="📰 每日摘要", content="GitHub...", level="daily", source="github_trending")

        # At limit (5/5), daily message should skip serverchan and go to email
        with patch.object(manager.serverchan, "push") as mock_serverchan:
            with patch.object(manager.email, "push", return_value=True) as mock_email:
                result = manager.push(msg)
                mock_serverchan.assert_not_called()
                mock_email.assert_called_once_with(msg)
                assert result.channel == "email"
                assert result.success is True

    def test_urgent_message_ignores_daily_limit(self):
        """Test that urgent messages bypass Server酱 daily limit."""
        mock_db = MagicMock()
        mock_db.get_push_count_today.return_value = 5  # Already at limit
        mock_db.save_push_log = MagicMock()

        serverchan_config = {"sendkey": "valid-key", "daily_limit": 5}
        email_config = {
            "smtp_host": "smtp.test.com",
            "smtp_port": 465,
            "from": "sender@test.com",
            "password": "test-password",
            "to": "receiver@test.com"
        }
        manager = PushManager(serverchan_config=serverchan_config, email_config=email_config, db=mock_db)

        msg = Message(title="🔴 UP主开播", content="xxx", level="urgent", source="bilibili_live")

        # Urgent message should still try serverchan even at limit
        with patch.object(manager.serverchan, "push", return_value=True) as mock_serverchan:
            result = manager.push(msg)
            mock_serverchan.assert_called_once_with(msg)
            assert result.channel == "serverchan"
            assert result.success is True

    def test_push_log_recorded_on_success(self):
        """Test that push log is recorded when push succeeds."""
        mock_db = MagicMock()
        mock_db.get_push_count_today.return_value = 0
        mock_db.save_push_log = MagicMock()

        serverchan_config = {"sendkey": "valid-key", "daily_limit": 5}
        email_config = {
            "smtp_host": "smtp.test.com",
            "smtp_port": 465,
            "from": "sender@test.com",
            "password": "test-password",
            "to": "receiver@test.com"
        }
        manager = PushManager(serverchan_config=serverchan_config, email_config=email_config, db=mock_db)

        msg = Message(title="Test", content="Content", level="urgent", source="test")

        with patch.object(manager.serverchan, "push", return_value=True):
            result = manager.push(msg)

            mock_db.save_push_log.assert_called_once()
            call_args = mock_db.save_push_log.call_args[1]
            assert call_args["channel"] == "serverchan"
            assert call_args["success"] is True

    def test_push_log_recorded_on_failure(self):
        """Test that push log is recorded even when all pushers fail."""
        mock_db = MagicMock()
        mock_db.get_push_count_today.return_value = 0
        mock_db.save_push_log = MagicMock()

        serverchan_config = {"sendkey": "valid-key", "daily_limit": 5}
        email_config = {
            "smtp_host": "smtp.test.com",
            "smtp_port": 465,
            "from": "sender@test.com",
            "password": "test-password",
            "to": "receiver@test.com"
        }
        manager = PushManager(serverchan_config=serverchan_config, email_config=email_config, db=mock_db)

        msg = Message(title="Test", content="Content", level="urgent", source="test")

        with patch.object(manager.serverchan, "push", return_value=False):
            with patch.object(manager.email, "push", return_value=False):
                result = manager.push(msg)
                assert result.success is False
                # Still should have logged the attempt
                assert mock_db.save_push_log.call_count == 2  # Both attempts logged