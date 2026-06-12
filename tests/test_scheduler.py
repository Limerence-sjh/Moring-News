"""Tests for MorningNewsScheduler - plugin orchestration, job registration, and daily summary."""

import pytest
from unittest.mock import MagicMock, patch
from morning_news.models import Message, PluginResult
from morning_news.plugins.base import BasePlugin
from morning_news.scheduler import MorningNewsScheduler


class MockIntervalPlugin(BasePlugin):
    name = "mock_interval"
    schedule_type = "interval"
    interval_minutes = 5

    def run(self, db):
        return PluginResult(
            messages=[
                Message(title="即时告警", content="测试", level="urgent", source=self.name)
            ],
            data={"checked": True},
        )


class MockCronPlugin(BasePlugin):
    name = "mock_cron"
    schedule_type = "cron"
    cron_expression = "0 18 * * *"

    def run(self, db):
        return PluginResult(
            messages=[
                Message(title="每日摘要", content="测试", level="daily", source=self.name)
            ],
            data={"daily_data": True},
        )


class MockCronPlugin2(BasePlugin):
    name = "mock_cron2"
    schedule_type = "cron"
    cron_expression = "0 18 * * *"

    def run(self, db):
        return PluginResult(
            messages=[
                Message(title="每日摘要2", content="测试2", level="daily", source=self.name)
            ],
            data={"daily_data2": True},
        )


def _make_config(
    instant_interval=5,
    daily_time="18:00",
    sources=None,
    serverchan_config=None,
    email_config=None,
):
    if sources is None:
        sources = {
            "mock_interval": {"enabled": True},
            "mock_cron": {"enabled": True},
        }
    if serverchan_config is None:
        serverchan_config = {"sendkey": "test-key", "daily_limit": 5}
    if email_config is None:
        email_config = {
            "smtp_host": "smtp.test.com",
            "smtp_port": 465,
            "from": "test@test.com",
            "password": "test-password",
            "to": "target@test.com",
        }
    return {
        "scheduler": {
            "instant_interval": instant_interval,
            "daily_time": daily_time,
        },
        "push": {
            "serverchan": serverchan_config,
            "email": email_config,
        },
        "sources": sources,
    }


def _mock_db():
    db = MagicMock()
    db.db_path = "/tmp/test_morning_news.db"
    return db


def _create_scheduler(config, db):
    with patch.object(MorningNewsScheduler, "_init_apscheduler"):
        with patch("morning_news.scheduler.PushManager") as mock_pm_cls:
            with patch("morning_news.scheduler.discover_plugins", return_value=_get_mock_plugins(config)):
                scheduler = MorningNewsScheduler(config=config, db=db)
    scheduler._apscheduler = MagicMock()
    return scheduler


def _get_mock_plugins(config):
    available = {
        "mock_interval": MockIntervalPlugin,
        "mock_cron": MockCronPlugin,
        "mock_cron2": MockCronPlugin2,
    }
    result = {}
    sources = config.get("sources", {})
    for name in sources:
        if name in available:
            result[name] = available[name]
    return result


class TestSchedulerInit:

    def test_scheduler_init_with_config(self):
        config = _make_config(instant_interval=10, daily_time="09:30")
        db = _mock_db()
        scheduler = _create_scheduler(config, db)

        assert scheduler.instant_interval == 10
        assert scheduler.daily_hour == 9
        assert scheduler.daily_minute == 30
        assert scheduler.config is config
        assert scheduler.db is db

    def test_scheduler_init_default_values(self):
        config = _make_config(instant_interval=5, daily_time="18:00")
        db = _mock_db()
        scheduler = _create_scheduler(config, db)

        assert scheduler.instant_interval == 5
        assert scheduler.daily_hour == 18
        assert scheduler.daily_minute == 0


class TestSchedulerLoadsPlugins:

    def test_scheduler_loads_enabled_plugins(self):
        config = _make_config(
            sources={"mock_interval": {"enabled": True}, "mock_cron": {"enabled": True}}
        )
        db = _mock_db()
        scheduler = _create_scheduler(config, db)

        assert "mock_interval" in scheduler.plugins
        assert "mock_cron" in scheduler.plugins
        assert isinstance(scheduler.plugins["mock_interval"], MockIntervalPlugin)
        assert isinstance(scheduler.plugins["mock_cron"], MockCronPlugin)

    def test_scheduler_skips_disabled_plugins(self):
        config = _make_config(
            sources={"mock_interval": {"enabled": False}}
        )
        db = _mock_db()
        scheduler = _create_scheduler(config, db)

        assert "mock_interval" not in scheduler.plugins

    def test_scheduler_warns_on_missing_plugin(self):
        config = _make_config(
            sources={"unknown_plugin": {"enabled": True}}
        )
        db = _mock_db()

        with patch("morning_news.scheduler.discover_plugins", return_value={}):
            with patch.object(MorningNewsScheduler, "_init_apscheduler"):
                with patch("morning_news.scheduler.PushManager"):
                    scheduler = MorningNewsScheduler(config=config, db=db)

        assert "unknown_plugin" not in scheduler.plugins


class TestRunSinglePluginWithUrgentMessage:

    def test_run_plugin_job_pushes_messages(self):
        config = _make_config(
            sources={"mock_interval": {"enabled": True}}
        )
        db = _mock_db()
        scheduler = _create_scheduler(config, db)

        mock_push_manager = scheduler.push_manager
        plugin = scheduler.plugins["mock_interval"]

        scheduler._run_plugin_job(plugin)

        assert mock_push_manager.push.call_count == 1
        pushed_msg = mock_push_manager.push.call_args[0][0]
        assert pushed_msg.level == "urgent"
        assert pushed_msg.source == "mock_interval"

    def test_run_plugin_job_handles_exception(self):
        config = _make_config(
            sources={"mock_interval": {"enabled": True}}
        )
        db = _mock_db()
        scheduler = _create_scheduler(config, db)

        plugin = scheduler.plugins["mock_interval"]

        with patch.object(plugin, "run", side_effect=Exception("boom")):
            scheduler._run_plugin_job(plugin)

        mock_push_manager = scheduler.push_manager
        mock_push_manager.push.assert_not_called()


class TestRunDailyPluginsAggregation:

    def test_run_daily_summary_aggregates_all_cron_plugins(self):
        config = _make_config(
            sources={"mock_cron": {"enabled": True}, "mock_cron2": {"enabled": True}}
        )
        db = _mock_db()
        scheduler = _create_scheduler(config, db)

        cron_plugins = [
            scheduler.plugins["mock_cron"],
            scheduler.plugins["mock_cron2"],
        ]

        scheduler._run_daily_summary_job(cron_plugins)

        mock_push_manager = scheduler.push_manager
        assert mock_push_manager.push.call_count == 1

        pushed_msg = mock_push_manager.push.call_args[0][0]
        assert pushed_msg.level == "daily"
        assert pushed_msg.source == "daily_summary"
        assert "每日摘要" in pushed_msg.content
        assert "每日摘要2" in pushed_msg.content
        assert "---" in pushed_msg.content


class TestDailySummaryMessageFormat:

    def test_daily_summary_title_format(self):
        config = _make_config(
            sources={"mock_cron": {"enabled": True}}
        )
        db = _mock_db()
        scheduler = _create_scheduler(config, db)

        cron_plugins = [scheduler.plugins["mock_cron"]]

        scheduler._run_daily_summary_job(cron_plugins)

        mock_push_manager = scheduler.push_manager
        pushed_msg = mock_push_manager.push.call_args[0][0]

        from datetime import date
        today = date.today().isoformat()
        assert pushed_msg.title == f"\U0001F4F0 Morning News 每日摘要 | {today}"
        assert pushed_msg.level == "daily"

    def test_daily_summary_sections_separated(self):
        config = _make_config(
            sources={"mock_cron": {"enabled": True}, "mock_cron2": {"enabled": True}}
        )
        db = _mock_db()
        scheduler = _create_scheduler(config, db)

        cron_plugins = [
            scheduler.plugins["mock_cron"],
            scheduler.plugins["mock_cron2"],
        ]

        scheduler._run_daily_summary_job(cron_plugins)

        pushed_msg = scheduler.push_manager.push.call_args[0][0]
        parts = pushed_msg.content.split("\n---\n")
        assert len(parts) == 2


class TestRegisterJobs:

    def test_register_interval_job(self):
        config = _make_config(
            instant_interval=15,
            sources={"mock_interval": {"enabled": True}},
        )
        db = _mock_db()
        scheduler = _create_scheduler(config, db)

        scheduler._register_jobs()

        mock_add_job = scheduler._apscheduler.add_job
        interval_calls = [
            c for c in mock_add_job.call_args_list
            if c[1].get("trigger") == "interval"
        ]
        assert len(interval_calls) == 1
        assert interval_calls[0][1]["minutes"] == 15
        assert interval_calls[0][1]["id"] == "plugin_mock_interval"

    def test_register_cron_job(self):
        config = _make_config(
            daily_time="09:30",
            sources={"mock_cron": {"enabled": True}},
        )
        db = _mock_db()
        scheduler = _create_scheduler(config, db)

        scheduler._register_jobs()

        mock_add_job = scheduler._apscheduler.add_job
        cron_calls = [
            c for c in mock_add_job.call_args_list
            if c[1].get("trigger") == "cron"
        ]
        assert len(cron_calls) == 1
        assert cron_calls[0][1]["hour"] == 9
        assert cron_calls[0][1]["minute"] == 30
        assert cron_calls[0][1]["id"] == "daily_summary"

    def test_register_both_interval_and_cron_jobs(self):
        config = _make_config(
            sources={"mock_interval": {"enabled": True}, "mock_cron": {"enabled": True}},
        )
        db = _mock_db()
        scheduler = _create_scheduler(config, db)

        scheduler._register_jobs()
        assert scheduler._apscheduler.add_job.call_count == 2