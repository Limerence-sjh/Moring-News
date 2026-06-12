"""Scheduler for Morning News - orchestrates plugin execution with APScheduler.

Manages two types of plugin scheduling:
- interval plugins: run periodically (e.g., every 5 minutes for live stream alerts)
- cron plugins: run once daily at a scheduled time for daily summaries
"""

import logging
from datetime import date
from typing import Dict, List, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor

from morning_news.models import Message, PluginResult
from morning_news.plugins import discover_plugins
from morning_news.plugins.base import BasePlugin
from morning_news.pusher.manager import PushManager

logger = logging.getLogger(__name__)


class MorningNewsScheduler:
    """Orchestrate plugin execution and message pushing with APScheduler.

    Args:
        config: Full config dict from ConfigLoader.
        db: Database instance for persisting data and push logs.
    """

    def __init__(self, config: dict, db):
        self.config = config
        self.db = db

        scheduler_config = config.get("scheduler", {})
        self.instant_interval: int = scheduler_config.get("instant_interval", 5)
        daily_time: str = scheduler_config.get("daily_time", "18:00")
        parts = daily_time.split(":")
        self.daily_hour: int = int(parts[0])
        self.daily_minute: int = int(parts[1])

        self.plugins: Dict[str, BasePlugin] = {}
        self.push_manager: Optional[PushManager] = None

        self._apscheduler: Optional[BackgroundScheduler] = None
        self._init_apscheduler()

        self._load_plugins()
        self._init_push_manager()

    def _load_plugins(self) -> None:
        plugin_classes = discover_plugins()

        sources = self.config.get("sources", {})
        for source_name, source_config in sources.items():
            if not source_config.get("enabled", True):
                continue

            plugin_cls = plugin_classes.get(source_name)
            if plugin_cls is None:
                logger.warning(
                    "Plugin '%s' not found in discovered plugins, skipping",
                    source_name,
                )
                continue

            plugin_instance = plugin_cls(source_config)
            self.plugins[source_name] = plugin_instance
            logger.info("Loaded plugin: %s", source_name)

    def _init_apscheduler(self) -> None:
        jobstores = {
            "default": SQLAlchemyJobStore(
                url=f"sqlite:///{self.db.db_path}_jobs"
            )
        }
        executors = {
            "default": ThreadPoolExecutor(max_workers=10)
        }
        self._apscheduler = BackgroundScheduler(
            jobstores=jobstores,
            executors=executors,
        )

    def _init_push_manager(self) -> None:
        push_config = self.config.get("push", {})
        serverchan_config = push_config.get("serverchan", {})
        email_config = push_config.get("email", {})
        self.push_manager = PushManager(
            serverchan_config=serverchan_config,
            email_config=email_config,
            db=self.db,
        )

    def _register_jobs(self) -> None:
        interval_plugins: List[BasePlugin] = []
        cron_plugins: List[BasePlugin] = []

        for plugin in self.plugins.values():
            if plugin.schedule_type == "interval":
                interval_plugins.append(plugin)
            elif plugin.schedule_type == "cron":
                cron_plugins.append(plugin)

        for plugin in interval_plugins:
            self._apscheduler.add_job(
                func=self._run_plugin_job,
                trigger="interval",
                minutes=self.instant_interval,
                id=f"plugin_{plugin.name}",
                args=[plugin],
            )
            logger.info(
                "Registered interval job for '%s' (every %d min)",
                plugin.name,
                self.instant_interval,
            )

        if cron_plugins:
            self._apscheduler.add_job(
                func=self._run_daily_summary_job,
                trigger="cron",
                hour=self.daily_hour,
                minute=self.daily_minute,
                id="daily_summary",
                args=[cron_plugins],
            )
            logger.info(
                "Registered daily summary job at %02d:%02d",
                self.daily_hour,
                self.daily_minute,
            )

    def _run_plugin_job(self, plugin: BasePlugin) -> None:
        try:
            result: PluginResult = plugin.run(self.db)
            for message in result.messages:
                self.push_manager.push(message)
            logger.info("Plugin '%s' completed: %d messages", plugin.name, len(result.messages))
        except Exception:
            logger.exception("Plugin '%s' failed", plugin.name)

    def _run_daily_summary_job(self, cron_plugins: List[BasePlugin]) -> None:
        content_parts: List[str] = []
        all_messages: List[Message] = []

        for plugin in cron_plugins:
            try:
                result: PluginResult = plugin.run(self.db)
                for message in result.messages:
                    content_parts.append(f"**{message.title}**\n{message.content}")
                    all_messages.append(message)
            except Exception:
                logger.exception("Cron plugin '%s' failed during daily summary", plugin.name)

        if not content_parts:
            logger.warning("No content from cron plugins for daily summary")
            return

        combined_content = "\n---\n".join(content_parts)
        today = date.today().isoformat()
        summary_message = Message(
            title=f"\U0001F4F0 Morning News 每日摘要 | {today}",
            content=combined_content,
            level="daily",
            source="daily_summary",
        )
        self.push_manager.push(summary_message)
        logger.info("Daily summary pushed with %d sections", len(content_parts))

    def start(self) -> None:
        self._register_jobs()
        self._apscheduler.start()
        logger.info("Scheduler started")

    def shutdown(self) -> None:
        self._apscheduler.shutdown(wait=True)
        logger.info("Scheduler shut down")

    def run_all_once(self) -> None:
        for plugin in self.plugins.values():
            try:
                result: PluginResult = plugin.run(self.db)
                for message in result.messages:
                    push_result = self.push_manager.push(message)
                    print(f"[{plugin.name}] {message.title}: {push_result.channel} ({push_result.success})")
                if result.data:
                    print(f"[{plugin.name}] data: {result.data}")
            except Exception as e:
                print(f"[{plugin.name}] ERROR: {e}")