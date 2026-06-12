"""Tests for push manager - priority routing and fallback logic."""

import pytest
from unittest.mock import MagicMock, patch
from morning_news.models import Message
from morning_news.pusher.manager import PushManager, PushResult
from morning_news.pusher.serverchan import ServerChanPusher
from morning_news.pusher.email import EmailPusher


class TestPushResult:

    def test_push_result_creation(self):
        result = PushResult(channel="serverchan", success=True, message_title="Test")
        assert result.channel == "serverchan"
        assert result.success is True
        assert result.message_title == "Test"

    def test_push_result_defaults(self):
        result = PushResult(channel="email", success=False)
        assert result.message_title == ""


class TestPushManagerInit:

    def test_manager_init_with_pushers(self):
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
        mock_db = MagicMock()
        mock_db.get_push_count_today.return_value = 4
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

        with patch.object(manager.serverchan, "push", return_value=True) as mock_serverchan:
            result = manager.push(msg)
            mock_serverchan.assert_called_once_with(msg)
            assert result.channel == "serverchan"

    def test_daily_message_goes_to_email_when_limit_reached(self):
        mock_db = MagicMock()
        mock_db.get_push_count_today.return_value = 5
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

        with patch.object(manager.serverchan, "push") as mock_serverchan:
            with patch.object(manager.email, "push", return_value=True) as mock_email:
                result = manager.push(msg)
                mock_serverchan.assert_not_called()
                mock_email.assert_called_once_with(msg)
                assert result.channel == "email"
                assert result.success is True

    def test_urgent_message_ignores_daily_limit(self):
        mock_db = MagicMock()
        mock_db.get_push_count_today.return_value = 5
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

        with patch.object(manager.serverchan, "push", return_value=True) as mock_serverchan:
            result = manager.push(msg)
            mock_serverchan.assert_called_once_with(msg)
            assert result.channel == "serverchan"
            assert result.success is True

    def test_push_log_recorded_on_success(self):
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
                assert mock_db.save_push_log.call_count == 2