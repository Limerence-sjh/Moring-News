"""Tests for models module."""

import pytest
from morning_news.models import Message, PluginResult


class TestMessage:

    def test_message_creation_with_all_fields(self):
        """Test creating a Message with all fields specified."""
        msg = Message(
            title="🔴 UP主A 开播了",
            content="直播间标题: 聊天",
            level="urgent",
            source="bilibili_live"
        )
        assert msg.title == "🔴 UP主A 开播了"
        assert msg.content == "直播间标题: 聊天"
        assert msg.level == "urgent"
        assert msg.source == "bilibili_live"

    def test_message_defaults(self):
        """Test Message default values for level and source."""
        msg = Message(title="Test title", content="Test content")
        assert msg.level == "daily"
        assert msg.source == ""

    def test_message_with_daily_level(self):
        """Test creating a daily-level Message."""
        msg = Message(
            title="📰 每日摘要",
            content="GitHub Trending top 10...",
            level="daily",
            source="github_trending"
        )
        assert msg.level == "daily"

    def test_message_invalid_level(self):
        """Test that invalid level raises ValueError."""
        with pytest.raises(ValueError, match="Invalid level"):
            Message(title="Test", content="Test", level="invalid", source="test")

    def test_message_to_dict(self):
        """Test Message serialization to dict."""
        msg = Message(title="Test", content="Body", level="urgent", source="bilibili_live")
        d = msg.to_dict()
        assert d["title"] == "Test"
        assert d["content"] == "Body"
        assert d["level"] == "urgent"
        assert d["source"] == "bilibili_live"


class TestPluginResult:

    def test_plugin_result_with_messages(self):
        """Test PluginResult containing messages."""
        msgs = [
            Message(title="Msg1", content="C1", level="urgent", source="test"),
            Message(title="Msg2", content="C2", level="daily", source="test"),
        ]
        result = PluginResult(messages=msgs, data={"key": "value"})
        assert len(result.messages) == 2
        assert result.messages[0].title == "Msg1"
        assert result.data == {"key": "value"}

    def test_plugin_result_with_empty_messages(self):
        """Test PluginResult with no messages (e.g., no state change)."""
        result = PluginResult(messages=[], data={"status": "no_change"})
        assert len(result.messages) == 0
        assert result.data["status"] == "no_change"

    def test_plugin_result_defaults(self):
        """Test PluginResult default values."""
        result = PluginResult()
        assert result.messages == []
        assert result.data == {}

    def test_plugin_result_has_messages_property(self):
        """Test has_messages convenience property."""
        result_with = PluginResult(
            messages=[Message(title="T", content="C")],
            data={}
        )
        result_empty = PluginResult(messages=[], data={})
        assert result_with.has_messages is True
        assert result_empty.has_messages is False