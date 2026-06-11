"""Shared test fixtures for Morning News."""

import os
import tempfile
import pytest
from morning_news.config_loader import ConfigLoader
from morning_news.db import Database


@pytest.fixture
def temp_dir():
    """Provide a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as d:
        yield d


@pytest.fixture
def sample_config_path(temp_dir):
    """Create a sample config.yaml in temp directory."""
    config_content = """
push:
  serverchan:
    sendkey: "test-sendkey-123"
    daily_limit: 5
  email:
    smtp_host: "smtp.test.com"
    smtp_port: 465
    from: "test@test.com"
    password: "test-password"
    to: "target@test.com"

scheduler:
  instant_interval: 5
  daily_time: "18:00"

sources:
  bilibili_live:
    enabled: true
    up_ids:
      - "12345"
      - "67890"
  github_trending:
    enabled: true
    top_count: 10
    language: ""
    since: "daily"
  weibo:
    enabled: true
    top_count: 5
"""
    config_path = os.path.join(temp_dir, "config.yaml")
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(config_content)
    return config_path


@pytest.fixture
def config(sample_config_path):
    """Load config from sample config file."""
    loader = ConfigLoader(sample_config_path)
    return loader.load()


@pytest.fixture
def db(temp_dir):
    """Create a test database in temp directory."""
    db_path = os.path.join(temp_dir, "test_morning_news.db")
    database = Database(db_path)
    database.initialize()
    return database