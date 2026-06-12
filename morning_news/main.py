"""CLI entry point for Morning News.

Provides command-line interface with --config, --initdb, --dry-run, --verbose options.
"""

import argparse
import logging
import os
import sys
import time

from morning_news.config_loader import ConfigLoader, ConfigError
from morning_news.db import Database
from morning_news.scheduler import MorningNewsScheduler

logger = logging.getLogger("morning_news")


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for the application.

    Args:
        verbose: If True, set level to DEBUG; otherwise INFO.
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Namespace with config, initdb, dry_run, verbose attributes.
    """
    parser = argparse.ArgumentParser(
        prog="morning_news",
        description="Morning News - 个人信息聚合推送工具",
    )
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to config YAML file (default: config.yaml)",
    )
    parser.add_argument(
        "--initdb",
        action="store_true",
        help="Initialize database and exit",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run all plugins once without scheduling and exit",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable DEBUG-level logging",
    )
    return parser.parse_args()


def main() -> None:
    """CLI entry point: parse args, load config, init db, run scheduler."""
    args = parse_args()
    setup_logging(verbose=args.verbose)

    try:
        config_loader = ConfigLoader(args.config)
        config = config_loader.load()
    except ConfigError as e:
        logger.error("Config error: %s", e)
        sys.exit(1)

    db_path = config.get("database", {}).get("path", "data/morning_news.db")
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    db = Database(db_path)

    if args.initdb:
        db.initialize()
        logger.info("Database initialized at %s", db_path)
        sys.exit(0)

    db.initialize()

    scheduler = MorningNewsScheduler(config, db)

    if args.dry_run:
        logger.info("Dry-run mode: executing all plugins once")
        scheduler.run_all_once()
        sys.exit(0)

    logger.info("Starting Morning News scheduler")
    scheduler.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Received KeyboardInterrupt, shutting down")
        scheduler.shutdown()