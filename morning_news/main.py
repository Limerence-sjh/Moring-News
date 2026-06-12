"""Morning News CLI entry point.

Usage:
    python -m morning_news --config config.yaml         # Start scheduler
    python -m morning_news --config config.yaml --initdb # Initialize database only
    python -m morning_news --config config.yaml --dry-run # Run all plugins once
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
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Morning News - 个人信息聚合推送工具",
        prog="morning_news"
    )
    parser.add_argument("--config", type=str, default="config.yaml", help="Path to config.yaml")
    parser.add_argument("--initdb", action="store_true", help="Initialize database and exit")
    parser.add_argument("--dry-run", action="store_true", help="Run all plugins once, then exit")
    parser.add_argument("--verbose", action="store_true", help="Enable DEBUG logging")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    setup_logging(verbose=args.verbose)

    try:
        loader = ConfigLoader(args.config)
        config = loader.load()
    except ConfigError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)

    db_path = config.get("database", {}).get("path", "data/morning_news.db")
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    db = Database(db_path)

    if args.initdb:
        logger.info(f"Initializing database at {db_path}")
        db.initialize()
        logger.info("Database initialized successfully")
        sys.exit(0)

    db.initialize()

    try:
        scheduler = MorningNewsScheduler(config=config, db=db)
    except Exception as e:
        logger.error(f"Failed to initialize scheduler: {e}")
        sys.exit(1)

    if args.dry_run:
        logger.info("Running in dry-run mode")
        scheduler.run_all_once()
        sys.exit(0)

    scheduler.start()
    logger.info("Morning News is running. Press Ctrl+C to stop.")

    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down...")
        scheduler.shutdown()
        logger.info("Goodbye!")