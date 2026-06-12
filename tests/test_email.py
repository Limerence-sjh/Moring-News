"""Tests for email pusher."""

import pytest
from unittest.mock import patch, MagicMock
from morning_news.models import Message
from morning_news.pusher.email import EmailPusher


class TestEmailPusherInit:

    def test_pusher_init_with_config(self):
        """Test pusher initialization with full SMTP config."""
        config = {
            "smtp_host": "smtp.test.com",
            "smtp_port": 465,
            "from": "sender@test.com",
            "password": "test-password",
            "to": "receiver@test.com"
        }
        pusher = EmailPusher(config)
        assert pusher.smtp_host == "smtp.test.com"
        assert pusher.smtp_port == 465
        assert pusher.from_addr == "sender@test.com"
        assert pusher.to_addr == "receiver@test.com"


class TestEmailPush:

    @patch("morning_news.pusher.email.smtplib.SMTP_SSL")
    def test_successful_push_returns_true(self, mock_smtp_ssl):
        """Test that a successful email push returns True."""
        mock_smtp = MagicMock()
        mock_smtp_ssl.return_value = mock_smtp

        config = {
            "smtp_host": "smtp.test.com",
            "smtp_port": 465,
            "from": "sender@test.com",
            "password": "test-password",
            "to": "receiver@test.com"
        }
        pusher = EmailPusher(config)
        msg = Message(title="测试标题", content="测试内容", level="urgent", source="test")
        result = pusher.push(msg)

        assert result is True
        mock_smtp.login.assert_called_once()
        mock_smtp.sendmail.assert_called_once()
        mock_smtp.quit.assert_called_once()

    @patch("morning_news.pusher.email.smtplib.SMTP_SSL")
    def test_push_handles_smtp_error(self, mock_smtp_ssl):
        """Test that push handles SMTP connection errors gracefully."""
        mock_smtp_ssl.side_effect = Exception("SMTP connection failed")

        config = {
            "smtp_host": "smtp.test.com",
            "smtp_port": 465,
            "from": "sender@test.com",
            "password": "test-password",
            "to": "receiver@test.com"
        }
        pusher = EmailPusher(config)
        msg = Message(title="测试", content="内容", level="urgent", source="test")
        result = pusher.push(msg)

        assert result is False

    @patch("morning_news.pusher.email.smtplib.SMTP_SSL")
    def test_push_handles_login_error(self, mock_smtp_ssl):
        """Test that push handles SMTP login errors gracefully."""
        mock_smtp = MagicMock()
        mock_smtp_ssl.return_value = mock_smtp
        mock_smtp.login.side_effect = Exception("Authentication failed")

        config = {
            "smtp_host": "smtp.test.com",
            "smtp_port": 465,
            "from": "sender@test.com",
            "password": "wrong-password",
            "to": "receiver@test.com"
        }
        pusher = EmailPusher(config)
        msg = Message(title="测试", content="内容", level="urgent", source="test")
        result = pusher.push(msg)

        assert result is False

    @patch("morning_news.pusher.email.smtplib.SMTP_SSL")
    def test_email_format_includes_html(self, mock_smtp_ssl):
        """Test that email push formats content as HTML."""
        mock_smtp = MagicMock()
        mock_smtp_ssl.return_value = mock_smtp

        config = {
            "smtp_host": "smtp.test.com",
            "smtp_port": 465,
            "from": "sender@test.com",
            "password": "test-password",
            "to": "receiver@test.com"
        }
        pusher = EmailPusher(config)
        msg = Message(title="标题", content="正文内容", level="daily", source="test")
        result = pusher.push(msg)

        assert result is True
        call_args = mock_smtp.sendmail.call_args
        email_body = call_args[0][2]
        assert "正文内容" in email_body
        assert "text/html" in email_body

    @patch("morning_news.pusher.email.smtplib.SMTP_SSL")
    def test_push_with_empty_config_returns_false(self, mock_smtp_ssl):
        """Test that push with empty SMTP config returns False."""
        config = {
            "smtp_host": "",
            "smtp_port": 465,
            "from": "",
            "password": "",
            "to": ""
        }
        pusher = EmailPusher(config)
        msg = Message(title="测试", content="内容", level="urgent", source="test")
        result = pusher.push(msg)

        assert result is False
        mock_smtp_ssl.assert_not_called()