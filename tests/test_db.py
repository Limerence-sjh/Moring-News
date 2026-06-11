"""Tests for database module."""

import os
import pytest
from morning_news.db import Database


class TestDatabaseInitialization:

    def test_database_creates_tables_on_init(self, db):
        """Test that initialize() creates all required tables."""
        tables = db._get_table_names()
        assert "push_log" in tables
        assert "bilibili_live_history" in tables
        assert "daily_data" in tables

    def test_database_file_created(self, temp_dir):
        """Test that initialize() creates the database file."""
        db_path = os.path.join(temp_dir, "test.db")
        db = Database(db_path)
        db.initialize()
        assert os.path.exists(db_path)


class TestBilibiliLiveHistory:

    def test_save_live_record(self, db):
        """Test saving a live room status record."""
        db.save_live_record(up_id="12345", title="聊天室", is_live=True)
        records = db.get_live_records(up_id="12345", limit=5)
        assert len(records) == 1
        assert records[0]["title"] == "聊天室"
        assert records[0]["is_live"] is True

    def test_save_multiple_live_records(self, db):
        """Test saving multiple records for the same UP主."""
        db.save_live_record(up_id="12345", title="聊天", is_live=True)
        db.save_live_record(up_id="12345", title="连麦答疑", is_live=True)
        records = db.get_live_records(up_id="12345", limit=5)
        assert len(records) == 2
        assert records[1]["title"] == "连麦答疑"

    def test_get_last_live_status_when_live(self, db):
        """Test getting the most recent live status when UP主 was live."""
        db.save_live_record(up_id="12345", title="直播中", is_live=True)
        status = db.get_last_live_status(up_id="12345")
        assert status["is_live"] is True
        assert status["title"] == "直播中"

    def test_get_last_live_status_when_offline(self, db):
        """Test getting the most recent live status when UP主 was offline."""
        db.save_live_record(up_id="12345", title="", is_live=False)
        status = db.get_last_live_status(up_id="12345")
        assert status["is_live"] is False

    def test_get_last_live_status_when_no_records(self, db):
        """Test getting last status when no records exist (assumed offline)."""
        status = db.get_last_live_status(up_id="99999")
        assert status["is_live"] is False
        assert status["title"] == ""

    def test_get_up_name_when_not_stored(self, db):
        """Test get_up_name returns UID when name is not stored."""
        name = db.get_up_name(up_id="12345")
        assert name == "12345"

    def test_save_and_get_up_name(self, db):
        """Test saving and retrieving UP主 display name."""
        db.save_up_name(up_id="12345", name="测试UP主")
        name = db.get_up_name(up_id="12345")
        assert name == "测试UP主"


class TestDailyData:

    def test_save_daily_data(self, db):
        """Test saving daily summary data for a source."""
        db.save_daily_data(
            source="github_trending",
            date="2026-06-10",
            data={"repos": [{"name": "test-repo", "stars": 100}]}
        )
        result = db.get_daily_data(source="github_trending", date="2026-06-10")
        assert result is not None
        assert result["repos"][0]["name"] == "test-repo"

    def test_get_daily_data_missing_date(self, db):
        """Test getting daily data for a date with no data."""
        result = db.get_daily_data(source="github_trending", date="2026-06-01")
        assert result is None

    def test_update_daily_data(self, db):
        """Test that saving daily data twice overwrites the previous data."""
        db.save_daily_data(source="weibo", date="2026-06-10", data={"top1": "旧热搜"})
        db.save_daily_data(source="weibo", date="2026-06-10", data={"top1": "新热搜"})
        result = db.get_daily_data(source="weibo", date="2026-06-10")
        assert result["top1"] == "新热搜"


class TestPushLog:

    def test_save_push_log(self, db):
        """Test recording a push log entry."""
        db.save_push_log(
            channel="serverchan",
            level="urgent",
            source="bilibili_live",
            title="🔴 UP主开播",
            content="直播间标题: xxx",
            success=True
        )
        count = db.get_push_count_today(channel="serverchan")
        assert count == 1

    def test_push_count_today_multiple_entries(self, db):
        """Test counting multiple push entries today."""
        db.save_push_log(channel="serverchan", level="urgent", source="test1", title="T1", content="C1", success=True)
        db.save_push_log(channel="serverchan", level="urgent", source="test2", title="T2", content="C2", success=True)
        db.save_push_log(channel="serverchan", level="daily", source="daily_summary", title="T3", content="C3", success=True)
        count = db.get_push_count_today(channel="serverchan")
        assert count == 3

    def test_push_count_today_different_channels(self, db):
        """Test that push count is per-channel."""
        db.save_push_log(channel="serverchan", level="urgent", source="test", title="T", content="C", success=True)
        db.save_push_log(channel="email", level="daily", source="test", title="T", content="C", success=True)
        serverchan_count = db.get_push_count_today(channel="serverchan")
        email_count = db.get_push_count_today(channel="email")
        assert serverchan_count == 1
        assert email_count == 1

    def test_push_count_empty(self, db):
        """Test push count when no pushes have been made."""
        count = db.get_push_count_today(channel="serverchan")
        assert count == 0

    def test_get_recent_push_logs(self, db):
        """Test retrieving recent push log entries."""
        db.save_push_log(channel="serverchan", level="urgent", source="bilibili_live", title="开播", content="xxx", success=True)
        db.save_push_log(channel="email", level="daily", source="github_trending", title="摘要", content="yyy", success=False)
        logs = db.get_recent_push_logs(limit=10)
        assert len(logs) == 2
        assert logs[0]["channel"] == "serverchan"
        assert logs[1]["success"] is False