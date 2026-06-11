# Morning News Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a personal information aggregation and push tool with B站开播通知, GitHub Trending, and 微博热搜, pushing via Server酱(WeChat) with email fallback.

**Architecture:** Plugin-based Python system with APScheduler scheduling, SQLite persistence, and a layered push system with priority/fallback logic. Each info source is an independent plugin following a unified interface.

**Tech Stack:** Python 3.10+, APScheduler 3.x, requests, BeautifulSoup4, PyYAML, SQLite, pytest, Server酱 API, SMTP

---

## File Structure

```
D:\work\Morning News/
├── morning_news/              # Python package
│   ├── __init__.py
│   ├── main.py                # Entry point, CLI
│   ├── config_loader.py       # Load and validate config.yaml
│   ├── scheduler.py           # APScheduler setup and plugin orchestration
│   ├── db.py                  # SQLite database operations
│   ├── models.py              # Message and PluginResult models
│   ├── pusher/
│   │   ├── __init__.py
│   │   ├── serverchan.py      # Server酱 push implementation
│   │   ├── email.py           # Email push implementation
│   │   └── manager.py         # Push manager: priority, fallback, daily limit
│   ├── plugins/
│   │   ├── __init__.py        # Auto-discovery of plugins
│   │   ├── base.py            # BasePlugin abstract class
│   │   ├── bilibili_live.py   # B站UP主开播+标题采集
│   │   ├── github_trending.py # GitHub Trending
│   │   ├── weibo_hot.py       # 微博热搜
│   │   ├── template.py        # Minimal template for new plugins
├── config.yaml                # User configuration
├── tests/
│   ├── __init__.py
│   ├── conftest.py            # Shared fixtures
│   ├── test_config_loader.py
│   ├── test_db.py
│   ├── test_models.py
│   ├── test_serverchan.py
│   ├── test_email.py
│   ├── test_push_manager.py
│   ├── test_bilibili_live.py
│   ├── test_github_trending.py
│   ├── test_weibo_hot.py
│   ├── test_scheduler.py
├── requirements.txt
├── README.md
├── config.example.yaml        # Example config for new users
├── data/                      # SQLite DB files (gitignored)
├── logs/                      # Log files (gitignored)
├── docs/
│   └── superpowers/
│       ├── specs/
│       │   └── 2026-06-10-morning-news-design.md
│       └── plans/
│           └── 2026-06-10-morning-news-phase1.md
```

---

### Task 1: Project Foundation

**Files:**
- Create: `requirements.txt`
- Create: `config.example.yaml`
- Create: `config.yaml`
- Create: `morning_news/__init__.py`
- Create: `morning_news/pusher/__init__.py`
- Create: `morning_news/plugins/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `.gitignore`
- Create: `README.md`

- [ ] **Step 1: Create project directories**

```bash
mkdir -p morning_news/pusher morning_news/plugins tests data logs
```

- [ ] **Step 2: Write requirements.txt**

Create `requirements.txt`:

```
apscheduler>=3.10.0
requests>=2.28.0
beautifulsoup4>=4.12.0
PyYAML>=6.0
lxml>=4.9.0
pytest>=7.0.0
```

- [ ] **Step 3: Write .gitignore**

Create `.gitignore`:

```
__pycache__/
*.pyc
*.pyo
data/
logs/
*.db
.env
.idea/
.vscode/
*.egg-info/
dist/
build/
```

- [ ] **Step 4: Write config.example.yaml**

Create `config.example.yaml`:

```yaml
# Morning News 配置文件示例
# 复制此文件为 config.yaml 并填入你的真实配置

# 推送渠道
push:
  serverchan:
    sendkey: "your-sendkey-here"    # 在 https://sct.ftqq.com/ 获取
    daily_limit: 5                  # 免费版每日推送上限
  email:
    smtp_host: "smtp.gmail.com"
    smtp_port: 465
    from: "your-email@gmail.com"
    password: "your-app-password"
    to: "target-email@gmail.com"

# 调度配置
scheduler:
  instant_interval: 5    # 即时源轮询间隔(分钟)
  daily_time: "18:00"    # 每日摘要推送时间

# 信息源配置
sources:
  bilibili_live:
    enabled: true
    up_ids:
      - "12345"           # 填入你关注的UP主UID
  github_trending:
    enabled: true
    top_count: 10
    language: ""           # 空=所有语言，可填 "python" 等
    since: "daily"         # daily / weekly / monthly
  weibo:
    enabled: true
    top_count: 5           # 取前5条热搜
```

- [ ] **Step 5: Write config.yaml (copy from example)**

Create `config.yaml` with the same structure as config.example.yaml, with sendkey and other fields left empty for the user to fill in:

```yaml
push:
  serverchan:
    sendkey: ""
    daily_limit: 5
  email:
    smtp_host: "smtp.gmail.com"
    smtp_port: 465
    from: ""
    password: ""
    to: ""

scheduler:
  instant_interval: 5
  daily_time: "18:00"

sources:
  bilibili_live:
    enabled: true
    up_ids:
      - ""
  github_trending:
    enabled: true
    top_count: 10
    language: ""
    since: "daily"
  weibo:
    enabled: true
    top_count: 5
```

- [ ] **Step 6: Write morning_news/__init__.py**

Create `morning_news/__init__.py`:

```python
"""Morning News - 个人信息聚合推送工具"""

__version__ = "0.1.0"
```

- [ ] **Step 7: Write morning_news/pusher/__init__.py**

Create `morning_news/pusher/__init__.py`:

```python
"""推送模块 - Server酱(微信) + 適件"""
```

- [ ] **Step 8: Write morning_news/plugins/__init__.py**

Create `morning_news/plugins/__init__.py` (placeholder, will be filled in Task 5):

```python
"""插件模块 - 信息源采集"""
```

- [ ] **Step 9: Write tests/__init__.py**

Create `tests/__init__.py` (empty):

```python
```

- [ ] **Step 10: Write tests/conftest.py**

Create `tests/conftest.py`:

```python
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
```

- [ ] **Step 11: Write README.md skeleton**

Create `README.md`:

```markdown
# Morning News 📰

个人信息聚合推送工具 —— 每天定时获取全网关注的信息，推送到微信/邮件。

## 功能

- 🔴 B站UP主开播即时通知
- 🚀 GitHub Trending 每日摘要
- 🔥 微博热搜每日摘要
- 📌 知乎热榜每日摘要 (Phase 3)
- 📊 指南针活跃市值阈值告警 (Phase 2)

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 编辑配置
cp config.example.yaml config.yaml
# 填入你的 Server酱 SendKey 和其他配置

# 初始化数据库
python -m morning_news --initdb

# 启动服务
python -m morning_news --config config.yaml

# 测试运行(只跑一次，不启动调度)
python -m morning_news --dry-run
```

## 配置说明

见 `config.example.yaml`

## 添加新的信息源

1. 在 `morning_news/plugins/` 下创建新的 `.py` 文件
2. 继承 `BasePlugin`，实现 `run()` 方法
3. 在 `config.yaml` 的 `sources` 下添加配置段
4. 重启服务

## 开发状态

| Phase | 功能 | 状态 |
|-------|------|------|
| Phase 1 | B站+GitHub+微博 | 🚧 开发中 |
| Phase 2 | 指南针活跃市值 | ⏳ 待研究 |
| Phase 3 | 知乎+多用户 | ⏳ 计划中 |
```

- [ ] **Step 12: Install dependencies**

```bash
pip install -r requirements.txt
```

- [ ] **Step 13: Verify project structure**

```bash
ls -R morning_news/ tests/
python -c "import morning_news; print(morning_news.__version__)"
```

Expected: directory listing shows all created files, version prints "0.1.0"

- [ ] **Step 14: Commit**

```bash
git add -A
git commit -m "feat: project foundation - directories, config, requirements, README"
```

---

### Task 2: Config Loader

**Files:**
- Create: `morning_news/config_loader.py`
- Create: `tests/test_config_loader.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_config_loader.py`:

```python
"""Tests for config_loader module."""

import os
import tempfile
import pytest
from morning_news.config_loader import ConfigLoader, ConfigError


class TestConfigLoader:

    def test_load_valid_config(self, sample_config_path):
        """Test loading a valid config.yaml file."""
        loader = ConfigLoader(sample_config_path)
        config = loader.load()
        assert config["push"]["serverchan"]["sendkey"] == "test-sendkey-123"
        assert config["push"]["serverchan"]["daily_limit"] == 5
        assert config["scheduler"]["instant_interval"] == 5
        assert config["scheduler"]["daily_time"] == "18:00"

    def test_access_sources_config(self, sample_config_path):
        """Test accessing source-specific configuration."""
        loader = ConfigLoader(sample_config_path)
        config = loader.load()
        assert config["sources"]["bilibili_live"]["enabled"] is True
        assert config["sources"]["bilibili_live"]["up_ids"] == ["12345", "67890"]
        assert config["sources"]["weibo"]["top_count"] == 5

    def test_missing_config_file_raises_error(self):
        """Test that missing config file raises ConfigError."""
        loader = ConfigLoader("/nonexistent/path/config.yaml")
        with pytest.raises(ConfigError, match="Config file not found"):
            loader.load()

    def test_missing_required_field_raises_error(self, temp_dir):
        """Test that missing required fields raise ConfigError."""
        config_content = """
push:
  serverchan:
    sendkey: "test-key"
    # missing daily_limit
  email:
    smtp_host: "smtp.test.com"
    smtp_port: 465
    from: "test@test.com"
    password: "test"
    to: "target@test.com"

scheduler:
  instant_interval: 5
  daily_time: "18:00"

sources:
  bilibili_live:
    enabled: true
    up_ids: ["12345"]
"""
        config_path = os.path.join(temp_dir, "config.yaml")
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(config_content)

        loader = ConfigLoader(config_path)
        # daily_limit has a default, so this should not raise
        config = loader.load()
        assert config["push"]["serverchan"]["daily_limit"] == 5  # default value

    def test_empty_config_raises_error(self, temp_dir):
        """Test that an empty config file raises ConfigError."""
        config_path = os.path.join(temp_dir, "config.yaml")
        with open(config_path, "w", encoding="utf-8") as f:
            f.write("")
        loader = ConfigLoader(config_path)
        with pytest.raises(ConfigError, match="Config file is empty"):
            loader.load()

    def test_invalid_yaml_raises_error(self, temp_dir):
        """Test that invalid YAML syntax raises ConfigError."""
        config_path = os.path.join(temp_dir, "config.yaml")
        with open(config_path, "w", encoding="utf-8") as f:
            f.write("invalid: yaml: [broken: {syntax}}]")
        loader = ConfigLoader(config_path)
        with pytest.raises(ConfigError, match="Invalid YAML"):
            loader.load()

    def test_get_source_config_method(self, sample_config_path):
        """Test the get_source_config convenience method."""
        loader = ConfigLoader(sample_config_path)
        config = loader.load()
        bilibili_config = loader.get_source_config(config, "bilibili_live")
        assert bilibili_config["up_ids"] == ["12345", "67890"]
        assert bilibili_config["enabled"] is True

    def test_get_source_config_missing_source(self, sample_config_path):
        """Test get_source_config for a source not in config."""
        loader = ConfigLoader(sample_config_path)
        config = loader.load()
        unknown_config = loader.get_source_config(config, "unknown_source")
        assert unknown_config is None
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_config_loader.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'morning_news.config_loader'"

- [ ] **Step 3: Write ConfigLoader implementation**

Create `morning_news/config_loader.py`:

```python
"""Configuration loader for Morning News.

Loads and validates config.yaml, providing dict-like access to configuration values.
"""

import os
import yaml


class ConfigError(Exception):
    """Raised when configuration is invalid or missing."""
    pass


class ConfigLoader:
    """Load and validate Morning News configuration from YAML file.

    Args:
        config_path: Path to config.yaml file.

    Raises:
        ConfigError: If file is missing, empty, or contains invalid YAML.
    """

    REQUIRED_TOP_KEYS = ["push", "scheduler", "sources"]
    DEFAULT_VALUES = {
        "push.serverchan.daily_limit": 5,
        "scheduler.instant_interval": 5,
        "scheduler.daily_time": "18:00",
    }

    def __init__(self, config_path: str):
        self.config_path = config_path

    def load(self) -> dict:
        """Load config.yaml and return validated config dict.

        Returns:
            Validated configuration dictionary.

        Raises:
            ConfigError: If file not found, empty, invalid YAML, or missing required keys.
        """
        if not os.path.exists(self.config_path):
            raise ConfigError(f"Config file not found: {self.config_path}")

        with open(self.config_path, "r", encoding="utf-8") as f:
            content = f.read()

        if not content.strip():
            raise ConfigError("Config file is empty")

        try:
            config = yaml.safe_load(content)
        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML: {e}")

        if config is None:
            raise ConfigError("Config file is empty")

        # Validate required top-level keys
        for key in self.REQUIRED_TOP_KEYS:
            if key not in config:
                raise ConfigError(f"Missing required config key: {key}")

        # Apply default values for missing optional fields
        self._apply_defaults(config)

        return config

    def get_source_config(self, config: dict, source_name: str) -> dict | None:
        """Get configuration for a specific source.

        Args:
            config: Full config dict.
            source_name: Name of the source (e.g., 'bilibili_live').

        Returns:
            Source config dict, or None if source not found.
        """
        sources = config.get("sources", {})
        return sources.get(source_name)

    def _apply_defaults(self, config: dict) -> None:
        """Apply default values for missing optional configuration fields.

        Args:
            config: Config dict to fill with defaults.
        """
        # Server酱 daily_limit default
        serverchan = config.get("push", {}).get("serverchan", {})
        if "daily_limit" not in serverchan:
            serverchan["daily_limit"] = self.DEFAULT_VALUES["push.serverchan.daily_limit"]

        # Scheduler defaults
        scheduler = config.get("scheduler", {})
        if "instant_interval" not in scheduler:
            scheduler["instant_interval"] = self.DEFAULT_VALUES["scheduler.instant_interval"]
        if "daily_time" not in scheduler:
            scheduler["daily_time"] = self.DEFAULT_VALUES["scheduler.daily_time"]
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_config_loader.py -v
```

Expected: All 8 tests PASS

- [ ] **Step 5: Commit**

```bash
git add morning_news/config_loader.py tests/test_config_loader.py
git commit -m "feat: add config loader with YAML validation and defaults"
```

---

### Task 3: Message Model

**Files:**
- Create: `morning_news/models.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_models.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_models.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'morning_news.models'"

- [ ] **Step 3: Write Message and PluginResult implementation**

Create `morning_news/models.py`:

```python
"""Data models for Morning News.

Defines Message (for push notifications) and PluginResult (for plugin output).
"""

from dataclasses import dataclass, field


VALID_LEVELS = ("urgent", "daily")


@dataclass
class Message:
    """A push notification message.

    Args:
        title: Message headline (shown in push notification).
        content: Message body text (may include Markdown).
        level: Priority level - 'urgent' for instant alerts, 'daily' for summaries.
        source: Name of the plugin that generated this message.
    """

    title: str
    content: str
    level: str = "daily"
    source: str = ""

    def __post_init__(self):
        """Validate level after initialization."""
        if self.level not in VALID_LEVELS:
            raise ValueError(
                f"Invalid level '{self.level}'. Must be one of: {VALID_LEVELS}"
            )

    def to_dict(self) -> dict:
        """Serialize Message to dictionary.

        Returns:
            Dict representation of the message.
        """
        return {
            "title": self.title,
            "content": self.content,
            "level": self.level,
            "source": self.source,
        }


@dataclass
class PluginResult:
    """Output from a plugin run.

    Args:
        messages: List of Message objects to be pushed immediately.
        data: Arbitrary dict of data to persist in database (for daily summary).
    """

    messages: list[Message] = field(default_factory=list)
    data: dict = field(default_factory=dict)

    @property
    def has_messages(self) -> bool:
        """Check if this result contains any messages to push.

        Returns:
            True if there are messages, False otherwise.
        """
        return len(self.messages) > 0
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_models.py -v
```

Expected: All 7 tests PASS

- [ ] **Step 5: Commit**

```bash
git add morning_news/models.py tests/test_models.py
git commit -m "feat: add Message and PluginResult data models"
```

---

### Task 4: Database Module

**Files:**
- Create: `morning_news/db.py`
- Create: `tests/test_db.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_db.py`:

```python
"""Tests for database module."""

import os
import pytest
from morning_news.db import Database


class TestDatabaseInitialization:

    def test_database_creates_tables_on_init(self, db):
        """Test that initialize() creates all required tables."""
        # Check tables exist by querying them
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_db.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'morning_news.db'"

- [ ] **Step 3: Write Database implementation**

Create `morning_news/db.py`:

```python
"""Database module for Morning News.

Manages SQLite database for persisting plugin data, push logs, and daily summaries.
"""

import json
import sqlite3
from datetime import datetime, date


class Database:
    """SQLite database manager for Morning News.

    Args:
        db_path: Path to the SQLite database file.
    """

    SCHEMA = """
    CREATE TABLE IF NOT EXISTS push_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        channel TEXT NOT NULL,
        level TEXT NOT NULL,
        source TEXT NOT NULL,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        success BOOLEAN NOT NULL
    );

    CREATE TABLE IF NOT EXISTS bilibili_live_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        up_id TEXT NOT NULL,
        title TEXT DEFAULT '',
        is_live BOOLEAN NOT NULL,
        UNIQUE(timestamp, up_id)
    );

    CREATE TABLE IF NOT EXISTS up_names (
        up_id TEXT PRIMARY KEY,
        name TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS daily_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT NOT NULL,
        date DATE NOT NULL,
        data_json TEXT NOT NULL,
        UNIQUE(source, date)
    );
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn = None

    def initialize(self) -> None:
        """Create database file and tables if they don't exist."""
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(self.SCHEMA)
        self._conn.commit()

    def _get_connection(self) -> sqlite3.Connection:
        """Get or create database connection.

        Returns:
            Active SQLite connection.
        """
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
        return self._conn

    def _get_table_names(self) -> list[str]:
        """Get list of all tables in the database.

        Returns:
            List of table names.
        """
        conn = self._get_connection()
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        return [row["name"] for row in cursor.fetchall()]

    # --- B站直播历史记录 ---

    def save_live_record(self, up_id: str, title: str, is_live: bool) -> None:
        """Save a live room status record for a UP主.

        Args:
            up_id: B站UP主UID.
            title: Current live room title.
            is_live: Whether the UP主 is currently streaming.
        """
        conn = self._get_connection()
        conn.execute(
            "INSERT OR REPLACE INTO bilibili_live_history (timestamp, up_id, title, is_live) VALUES (?, ?, ?, ?)",
            (datetime.now().isoformat(), up_id, title, is_live)
        )
        conn.commit()

    def get_live_records(self, up_id: str, limit: int = 10) -> list[dict]:
        """Get recent live status records for a UP主.

        Args:
            up_id: B站UP主UID.
            limit: Maximum number of records to return.

        Returns:
            List of record dicts with keys: id, timestamp, up_id, title, is_live.
        """
        conn = self._get_connection()
        cursor = conn.execute(
            "SELECT * FROM bilibili_live_history WHERE up_id=? ORDER BY timestamp DESC LIMIT ?",
            (up_id, limit)
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_last_live_status(self, up_id: str) -> dict:
        """Get the most recent live status for a UP主.

        If no records exist, returns a default offline status.

        Args:
            up_id: B站UP主UID.

        Returns:
            Dict with keys: is_live (bool), title (str).
        """
        conn = self._get_connection()
        cursor = conn.execute(
            "SELECT is_live, title FROM bilibili_live_history WHERE up_id=? ORDER BY timestamp DESC LIMIT 1",
            (up_id,)
        )
        row = cursor.fetchone()
        if row is None:
            return {"is_live": False, "title": ""}
        return {"is_live": bool(row["is_live"]), "title": row["title"]}

    def save_up_name(self, up_id: str, name: str) -> None:
        """Save or update UP主 display name.

        Args:
            up_id: B站UP主UID.
            name: Display name of the UP主.
        """
        conn = self._get_connection()
        conn.execute(
            "INSERT OR REPLACE INTO up_names (up_id, name) VALUES (?, ?)",
            (up_id, name)
        )
        conn.commit()

    def get_up_name(self, up_id: str) -> str:
        """Get UP主 display name, falling back to UID if not stored.

        Args:
            up_id: B站UP主UID.

        Returns:
            Display name string, or UID if name not stored.
        """
        conn = self._get_connection()
        cursor = conn.execute(
            "SELECT name FROM up_names WHERE up_id=?",
            (up_id,)
        )
        row = cursor.fetchone()
        if row is None:
            return up_id
        return row["name"]

    # --- 每日数据 ---

    def save_daily_data(self, source: str, date: str, data: dict) -> None:
        """Save daily summary data for a source.

        Args:
            source: Plugin name (e.g., 'github_trending').
            date: Date string in YYYY-MM-DD format.
            data: Dict of daily summary data (stored as JSON).
        """
        conn = self._get_connection()
        conn.execute(
            "INSERT OR REPLACE INTO daily_data (source, date, data_json) VALUES (?, ?, ?)",
            (source, date, json.dumps(data))
        )
        conn.commit()

    def get_daily_data(self, source: str, date: str) -> dict | None:
        """Get daily summary data for a source on a specific date.

        Args:
            source: Plugin name.
            date: Date string in YYYY-MM-DD format.

        Returns:
            Dict of daily data, or None if no data exists for that date.
        """
        conn = self._get_connection()
        cursor = conn.execute(
            "SELECT data_json FROM daily_data WHERE source=? AND date=?",
            (source, date)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return json.loads(row["data_json"])

    # --- 推送日志 ---

    def save_push_log(
        self,
        channel: str,
        level: str,
        source: str,
        title: str,
        content: str,
        success: bool
    ) -> None:
        """Record a push attempt in the log.

        Args:
            channel: Push channel ('serverchan' or 'email').
            level: Message level ('urgent' or 'daily').
            source: Plugin name that generated the message.
            title: Message title.
            content: Message content.
            success: Whether the push succeeded.
        """
        conn = self._get_connection()
        conn.execute(
            "INSERT INTO push_log (timestamp, channel, level, source, title, content, success) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (datetime.now().isoformat(), channel, level, source, title, content, success)
        )
        conn.commit()

    def get_push_count_today(self, channel: str) -> int:
        """Get the number of pushes made today through a specific channel.

        Args:
            channel: Push channel to count ('serverchan' or 'email').

        Returns:
            Number of push entries for today on that channel.
        """
        conn = self._get_connection()
        today = date.today().isoformat()
        cursor = conn.execute(
            "SELECT COUNT(*) FROM push_log WHERE channel=? AND timestamp >= ?",
            (channel, today)
        )
        row = cursor.fetchone()
        return row[0]

    def get_recent_push_logs(self, limit: int = 20) -> list[dict]:
        """Get recent push log entries.

        Args:
            limit: Maximum number of entries to return.

        Returns:
            List of push log dicts.
        """
        conn = self._get_connection()
        cursor = conn.execute(
            "SELECT * FROM push_log ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        )
        return [dict(row) for row in cursor.fetchall()]
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_db.py -v
```

Expected: All 14 tests PASS

- [ ] **Step 5: Commit**

```bash
git add morning_news/db.py tests/test_db.py
git commit -m "feat: add SQLite database module with live history, daily data, and push logs"
```

---

### Task 5: Plugin Base Class and Discovery

**Files:**
- Create: `morning_news/plugins/base.py`
- Modify: `morning_news/plugins/__init__.py`
- Create: `tests/test_plugin_base.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_plugin_base.py`:

```python
"""Tests for plugin base class and discovery."""

import os
import tempfile
import pytest
from morning_news.plugins.base import BasePlugin
from morning_news.models import PluginResult, Message
from morning_news.plugins import discover_plugins


class TestPluginBase:

    def test_base_plugin_is_abstract(self):
        """Test that BasePlugin cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            BasePlugin(config_section={})

    def test_plugin_subclass_instantiation(self):
        """Test that a proper subclass can be instantiated."""
        class TestPlugin(BasePlugin):
            name = "test_plugin"
            schedule_type = "interval"
            interval_minutes = 5

            def run(self, db):
                return PluginResult()

        plugin = TestPlugin(config_section={"enabled": True})
        assert plugin.name == "test_plugin"
        assert plugin.schedule_type == "interval"
        assert plugin.interval_minutes == 5
        assert plugin.enabled is True

    def test_plugin_subclass_with_cron(self):
        """Test a cron-type plugin subclass."""
        class CronPlugin(BasePlugin):
            name = "cron_plugin"
            schedule_type = "cron"
            cron_expression = "0 18 * * *"

            def run(self, db):
                return PluginResult()

        plugin = CronPlugin(config_section={"enabled": True})
        assert plugin.cron_expression == "0 18 * * *"

    def test_plugin_enabled_default_true(self):
        """Test that enabled defaults to True when config doesn't specify."""
        class TestPlugin(BasePlugin):
            name = "test"
            schedule_type = "interval"
            interval_minutes = 5

            def run(self, db):
                return PluginResult()

        plugin = TestPlugin(config_section={})
        assert plugin.enabled is True

    def test_plugin_enabled_false_from_config(self):
        """Test that enabled can be set to False from config."""
        class TestPlugin(BasePlugin):
            name = "test"
            schedule_type = "interval"
            interval_minutes = 5

            def run(self, db):
                return PluginResult()

        plugin = TestPlugin(config_section={"enabled": False})
        assert plugin.enabled is False


class TestDiscoverPlugins:

    def test_discover_plugins_finds_existing_plugins(self):
        """Test that discover_plugins finds plugin classes in the plugins directory."""
        plugins = discover_plugins()
        # Should at least find bilibili_live, github_trending, weibo_hot
        # (These will be created in later tasks)
        assert isinstance(plugins, dict)

    def test_discover_plugins_returns_name_to_class_mapping(self):
        """Test that discover_plugins returns {name: class} dict."""
        plugins = discover_plugins()
        for name, cls in plugins.items():
            assert isinstance(name, str)
            assert issubclass(cls, BasePlugin)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_plugin_base.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'morning_news.plugins.base'"

- [ ] **Step 3: Write BasePlugin implementation**

Create `morning_news/plugins/base.py`:

```python
"""Base plugin class for Morning News.

All info source plugins must inherit from BasePlugin and implement the run() method.
"""

from abc import ABC, abstractmethod
from morning_news.models import PluginResult


class BasePlugin(ABC):
    """Abstract base class for Morning News plugins.

    Every plugin must define:
    - name: Unique string identifier
    - schedule_type: 'interval' (periodic polling) or 'cron' (scheduled time)
    - run(): Method that executes data collection and returns results

    Args:
        config_section: Dict of plugin-specific configuration from config.yaml.
    """

    name: str = ""
    schedule_type: str = "interval"  # "interval" or "cron"
    interval_minutes: int = 5        # For interval-type plugins
    cron_expression: str = ""        # For cron-type plugins

    def __init__(self, config_section: dict):
        """Initialize plugin with its configuration section.

        Args:
            config_section: Plugin-specific config dict from config.yaml sources section.
        """
        self.enabled = config_section.get("enabled", True)
        self._config = config_section

    @abstractmethod
    def run(self, db) -> PluginResult:
        """Execute one data collection cycle.

        Args:
            db: Database instance for reading/writing state and history.

        Returns:
            PluginResult containing messages to push and data to persist.
        """
        ...
```

- [ ] **Step 4: Write plugin discovery in plugins/__init__.py**

Update `morning_news/plugins/__init__.py`:

```python
"""Plugin module for Morning News - auto-discovers and loads info source plugins."""

import importlib
import pkgutil
from morning_news.plugins.base import BasePlugin


def discover_plugins() -> dict[str, type[BasePlugin]]:
    """Discover all plugin classes in the plugins package.

    Scans morning_news.plugins for modules containing classes that inherit from BasePlugin.
    Returns a dict mapping plugin name to plugin class.

    Returns:
        Dict of {plugin_name: plugin_class} for all discovered plugins.
    """
    plugins = {}
    package_dir = __path__[0]

    for module_info in pkgutil.iter_modules([package_dir]):
        # Skip base module and template
        if module_info.name in ("base", "template"):
            continue

        try:
            module = importlib.import_module(f"morning_news.plugins.{module_info.name}")
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, BasePlugin)
                    and attr is not BasePlugin
                    and attr.name  # Must have a non-empty name
                ):
                    plugins[attr.name] = attr
        except ImportError:
            continue

    return plugins
```

- [ ] **Step 5: Run test to verify it passes**

```bash
pytest tests/test_plugin_base.py -v
```

Expected: All 6 tests PASS (discover_plugins may return empty dict since no concrete plugins exist yet, which is fine)

- [ ] **Step 6: Commit**

```bash
git add morning_news/plugins/base.py morning_news/plugins/__init__.py tests/test_plugin_base.py
git commit -m "feat: add BasePlugin abstract class and plugin auto-discovery"
```

---

### Task 6: B站 Plugin

**Files:**
- Create: `morning_news/plugins/bilibili_live.py`
- Create: `tests/test_bilibili_live.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_bilibili_live.py`:

```python
"""Tests for B站UP主开播 plugin."""

import json
import pytest
from unittest.mock import patch, MagicMock
from morning_news.plugins.bilibili_live import BilibiliLivePlugin
from morning_news.models import PluginResult


class TestBilibiliLivePluginInit:

    def test_plugin_init_with_config(self):
        """Test plugin initialization reads UP IDs from config."""
        config = {
            "enabled": True,
            "up_ids": ["12345", "67890"]
        }
        plugin = BilibiliLivePlugin(config_section=config)
        assert plugin.name == "bilibili_live"
        assert plugin.schedule_type == "interval"
        assert plugin.interval_minutes == 5
        assert plugin.up_ids == ["12345", "67890"]

    def test_plugin_enabled_from_config(self):
        """Test plugin enabled/disabled from config."""
        plugin_enabled = BilibiliLivePlugin(config_section={"enabled": True, "up_ids": ["1"]})
        plugin_disabled = BilibiliLivePlugin(config_section={"enabled": False, "up_ids": ["1"]})
        assert plugin_enabled.enabled is True
        assert plugin_disabled.enabled is False


class TestBilibiliLivePluginRun:

    def _mock_api_response(self, up_id, live_status, title=""):
        """Create a mock B站 API response for a single UP主.

        Args:
            up_id: UP主 UID.
            live_status: 0=offline, 1=live, 2=streaming.
            title: Live room title.
        """
        return {
            "code": 0,
            "msg": "success",
            "data": {
                str(up_id): {
                    "live_status": live_status,
                    "title": title,
                    "room_id": 12345,
                    "uname": f"UP主_{up_id}"
                }
            }
        }

    @patch("morning_news.plugins.bilibili_live.requests.post")
    def test_detect_live_transition_generates_urgent_message(self, mock_post, db):
        """Test that transition from offline to live generates an urgent message."""
        # UP主 was offline before (db has no records)
        # Now API returns live status
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self._mock_api_response("12345", 1, "连麦答疑")
        mock_post.return_value = mock_response

        config = {"enabled": True, "up_ids": ["12345"]}
        plugin = BilibiliLivePlugin(config_section=config)
        result = plugin.run(db)

        assert result.has_messages is True
        assert result.messages[0].level == "urgent"
        assert "开播了" in result.messages[0].title
        assert "连麦答疑" in result.messages[0].content

    @patch("morning_news.plugins.bilibili_live.requests.post")
    def test_no_message_when_already_online(self, mock_post, db):
        """Test no urgent message when UP主 was already live (no state change)."""
        # First run: UP主 goes online
        mock_response1 = MagicMock()
        mock_response1.status_code = 200
        mock_response1.json.return_value = self._mock_api_response("12345", 1, "聊天")
        mock_post.return_value = mock_response1

        config = {"enabled": True, "up_ids": ["12345"]}
        plugin = BilibiliLivePlugin(config_section=config)
        result1 = plugin.run(db)

        # Second run: UP主 still online, same status
        mock_response2 = MagicMock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = self._mock_api_response("12345", 1, "聊天")
        mock_post.return_value = mock_response2

        result2 = plugin.run(db)
        assert not result2.has_messages  # No new messages since status unchanged

    @patch("morning_news.plugins.bilibili_live.requests.post")
    def test_title_always_saved_to_db(self, mock_post, db):
        """Test that title is saved to DB even when no message is generated."""
        # UP主 was online before, still online now (no transition)
        db.save_live_record(up_id="12345", title="旧标题", is_live=True)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self._mock_api_response("12345", 1, "新标题")
        mock_post.return_value = mock_response

        config = {"enabled": True, "up_ids": ["12345"]}
        plugin = BilibiliLivePlugin(config_section=config)
        result = plugin.run(db)

        # No message (status unchanged), but title should be saved
        assert not result.has_messages
        last_status = db.get_last_live_status("12345")
        assert last_status["title"] == "新标题"

    @patch("morning_news.plugins.bilibili_live.requests.post")
    def test_multiple_up_ids(self, mock_post, db):
        """Test handling multiple UP IDs with different statuses."""
        api_data = {
            "code": 0,
            "msg": "success",
            "data": {
                "11111": {"live_status": 1, "title": "直播中", "room_id": 111, "uname": "UP_A"},
                "22222": {"live_status": 0, "title": "", "room_id": 222, "uname": "UP_B"},
            }
        }
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = api_data
        mock_post.return_value = mock_response

        config = {"enabled": True, "up_ids": ["11111", "22222"]}
        plugin = BilibiliLivePlugin(config_section=config)
        result = plugin.run(db)

        # Only UP_A (transition from offline to live) should generate a message
        assert result.has_messages is True
        urgent_msgs = [m for m in result.messages if m.level == "urgent"]
        assert len(urgent_msgs) == 1
        assert "UP_A" in urgent_msgs[0].title or "11111" in urgent_msgs[0].title

    @patch("morning_news.plugins.bilibili_live.requests.post")
    def test_api_error_returns_empty_messages(self, mock_post, db):
        """Test that API errors don't crash the plugin and return empty messages."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"code": -1, "msg": "error"}
        mock_post.return_value = mock_response

        config = {"enabled": True, "up_ids": ["12345"]}
        plugin = BilibiliLivePlugin(config_section=config)
        result = plugin.run(db)

        assert not result.has_messages  # No messages on API error

    @patch("morning_news.plugins.bilibili_live.requests.post")
    def test_network_error_returns_empty_messages(self, mock_post, db):
        """Test that network errors are handled gracefully."""
        mock_post.side_effect = Exception("Network error")

        config = {"enabled": True, "up_ids": ["12345"]}
        plugin = BilibiliLivePlugin(config_section=config)
        result = plugin.run(db)

        assert not result.has_messages  # No messages on network error
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_bilibili_live.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'morning_news.plugins.bilibili_live'"

- [ ] **Step 3: Write BilibiliLivePlugin implementation**

Create `morning_news/plugins/bilibili_live.py`:

```python
"""B站UP主开播通知 + 标题采集插件.

Monitors B站UP主直播状态 every 5 minutes:
- When UP主 transitions from offline to live → push urgent notification
- Every check: save current title to database for daily summary
"""

import requests
from morning_news.plugins.base import BasePlugin
from morning_news.models import Message, PluginResult


BILIBILI_LIVE_API = "https://api.live.bilibili.com/room/v1/Room/get_status_info_by_uids"


class BilibiliLivePlugin(BasePlugin):
    """Monitor B站UP主 live stream status and push notifications on开播.

    Config keys:
        up_ids: List of UP主 UID strings to monitor.
    """

    name = "bilibili_live"
    schedule_type = "interval"
    interval_minutes = 5

    def __init__(self, config_section: dict):
        """Initialize with UP主 IDs from config.

        Args:
            config_section: Dict with 'up_ids' list and optional 'enabled' flag.
        """
        super().__init__(config_section)
        self.up_ids = config_section.get("up_ids", [])

    def run(self, db) -> PluginResult:
        """Check live status for all monitored UP主s.

        For each UP主:
        1. Fetch current live status from B站 API
        2. Compare with last known status from database
        3. If transition from offline→live: create urgent Message
        4. Always save current title and status to database

        Args:
            db: Database instance for state persistence.

        Returns:
            PluginResult with urgent messages (if any) and current status data.
        """
        messages = []

        if not self.up_ids:
            return PluginResult(messages=[], data={})

        # Fetch all UP主s' status in one API call
        live_data = self._fetch_live_status()
        if live_data is None:
            return PluginResult(messages=[], data={"error": "api_fetch_failed"})

        for up_id in self.up_ids:
            up_data = live_data.get(str(up_id))
            if up_data is None:
                continue

            is_live = up_data.get("live_status", 0) in (1, 2)
            title = up_data.get("title", "")
            uname = up_data.get("uname", up_id)

            # Save UP主 name for better notifications
            db.save_up_name(up_id=up_id, name=uname)

            # Check if this is a transition from offline to live
            last_status = db.get_last_live_status(up_id=up_id)
            was_live = last_status["is_live"]

            if not was_live and is_live:
                messages.append(Message(
                    title=f"🔴 {uname} 开播了",
                    content=f"直播间标题: {title}",
                    level="urgent",
                    source=self.name
                ))

            # Always save current status and title to database
            db.save_live_record(up_id=up_id, title=title, is_live=is_live)

        return PluginResult(messages=messages, data={"checked_ups": self.up_ids})

    def _fetch_live_status(self) -> dict | None:
        """Fetch live status for all monitored UP主s from B站 API.

        Makes a single POST request with all UP IDs.

        Returns:
            Dict of {uid: status_data} from API, or None on error.
        """
        try:
            payload = {"uids": [int(uid) for uid in self.up_ids]}
            response = requests.post(
                BILIBILI_LIVE_API,
                json=payload,
                timeout=10
            )
            if response.status_code != 200:
                return None

            result = response.json()
            if result.get("code") != 0:
                return None

            return result.get("data", {})
        except Exception:
            return None
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_bilibili_live.py -v
```

Expected: All 7 tests PASS

- [ ] **Step 5: Commit**

```bash
git add morning_news/plugins/bilibili_live.py tests/test_bilibili_live.py
git commit -m "feat: add B站UP主开播通知 plugin with live status detection and title collection"
```

---

### Task 7: Server酱 Pusher

**Files:**
- Create: `morning_news/pusher/serverchan.py`
- Create: `tests/test_serverchan.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_serverchan.py`:

```python
"""Tests for Server酱 pusher."""

import pytest
from unittest.mock import patch, MagicMock
from morning_news.models import Message
from morning_news.pusher.serverchan import ServerChanPusher


class TestServerChanPusherInit:

    def test_pusher_init_with_config(self):
        """Test pusher initialization with valid config."""
        config = {
            "sendkey": "test-sendkey-123",
            "daily_limit": 5
        }
        pusher = ServerChanPusher(config)
        assert pusher.sendkey == "test-sendkey-123"
        assert pusher.daily_limit == 5

    def test_pusher_default_daily_limit(self):
        """Test pusher defaults daily_limit to 5."""
        config = {"sendkey": "test-key"}
        pusher = ServerChanPusher(config)
        assert pusher.daily_limit == 5


class TestServerChanPush:

    @patch("morning_news.pusher.serverchan.requests.post")
    def test_successful_push_returns_true(self, mock_post):
        """Test that a successful Server酱 push returns True."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"code": 0, "msg": "success"}
        mock_post.return_value = mock_response

        config = {"sendkey": "valid-key"}
        pusher = ServerChanPusher(config)
        msg = Message(title="测试标题", content="测试内容", level="urgent", source="test")
        result = pusher.push(msg)

        assert result is True
        # Verify the API call was made correctly
        call_args = mock_post.call_args
        assert "valid-key" in call_args[0][0]  # URL contains sendkey

    @patch("morning_news.pusher.serverchan.requests.post")
    def test_push_with_invalid_sendkey_returns_false(self, mock_post):
        """Test that push with invalid sendkey returns False."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"code": 40001, "msg": "invalid sendkey"}
        mock_post.return_value = mock_response

        config = {"sendkey": "invalid-key"}
        pusher = ServerChanPusher(config)
        msg = Message(title="测试", content="内容", level="urgent", source="test")
        result = pusher.push(msg)

        assert result is False

    @patch("morning_news.pusher.serverchan.requests.post")
    def test_push_handles_network_error(self, mock_post):
        """Test that push handles network errors gracefully and returns False."""
        mock_post.side_effect = Exception("Network timeout")

        config = {"sendkey": "any-key"}
        pusher = ServerChanPusher(config)
        msg = Message(title="测试", content="内容", level="urgent", source="test")
        result = pusher.push(msg)

        assert result is False

    @patch("morning_news.pusher.serverchan.requests.post")
    def test_push_handles_http_error_status(self, mock_post):
        """Test that push handles HTTP error status codes gracefully."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"code": -1, "msg": "server error"}
        mock_post.return_value = mock_response

        config = {"sendkey": "test-key"}
        pusher = ServerChanPusher(config)
        msg = Message(title="测试", content="内容", level="urgent", source="test")
        result = pusher.push(msg)

        assert result is False

    @patch("morning_news.pusher.serverchan.requests.post")
    def test_push_formats_markdown_content(self, mock_post):
        """Test that push sends content in markdown format."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"code": 0, "msg": "success"}
        mock_post.return_value = mock_response

        config = {"sendkey": "test-key"}
        pusher = ServerChanPusher(config)
        msg = Message(title="标题", content="# Markdown内容\n\n- 列表1\n- 列表2", level="daily", source="test")
        result = pusher.push(msg)

        assert result is True
        # Verify markdown content was passed as 'desp' parameter
        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["json"]["desp"] == "# Markdown内容\n\n- 列表1\n- 列表2"

    @patch("morning_news.pusher.serverchan.requests.post")
    def test_push_empty_sendkey_returns_false(self, mock_post):
        """Test that push with empty sendkey returns False without making API call."""
        config = {"sendkey": ""}
        pusher = ServerChanPusher(config)
        msg = Message(title="测试", content="内容", level="urgent", source="test")
        result = pusher.push(msg)

        assert result is False
        mock_post.assert_not_called()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_serverchan.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'morning_news.pusher.serverchan'"

- [ ] **Step 3: Write ServerChanPusher implementation**

Create `morning_news/pusher/serverchan.py`:

```python
"""Server酱 pusher for WeChat notifications.

Uses the Server酱 (SCTAPI) HTTP API to push messages to WeChat via official account.
Docs: https://sct.ftqq.com/
"""

import requests
from morning_news.models import Message


SERVERCHAN_API_URL = "https://sctapi.ftqq.com/{sendkey}.send"


class ServerChanPusher:
    """Push notifications to WeChat via Server酱.

    Args:
        config: Dict with 'sendkey' and optional 'daily_limit'.
    """

    def __init__(self, config: dict):
        """Initialize Server酱 pusher with config.

        Args:
            config: Must contain 'sendkey' string. 'daily_limit' defaults to 5.
        """
        self.sendkey = config.get("sendkey", "")
        self.daily_limit = config.get("daily_limit", 5)

    def push(self, message: Message) -> bool:
        """Push a message to WeChat via Server酱.

        Args:
            message: Message to push.

        Returns:
            True if push succeeded, False if push failed or sendkey is empty.
        """
        if not self.sendkey:
            return False

        url = SERVERCHAN_API_URL.format(sendkey=self.sendkey)

        try:
            response = requests.post(
                url,
                json={
                    "title": message.title,
                    "desp": message.content,  # Server酱 supports Markdown in 'desp'
                },
                timeout=15
            )

            if response.status_code != 200:
                return False

            result = response.json()
            return result.get("code") == 0

        except Exception:
            return False
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_serverchan.py -v
```

Expected: All 8 tests PASS

- [ ] **Step 5: Commit**

```bash
git add morning_news/pusher/serverchan.py tests/test_serverchan.py
git commit -m "feat: add Server酱 pusher for WeChat notifications"
```

---

### Task 8: Email Pusher

**Files:**
- Create: `morning_news/pusher/email.py`
- Create: `tests/test_email.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_email.py`:

```python
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
        # Verify email was sent
        call_args = mock_smtp.sendmail.call_args
        email_body = call_args[0][2]  # Third arg is the email body string
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_email.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'morning_news.pusher.email'"

- [ ] **Step 3: Write EmailPusher implementation**

Create `morning_news/pusher/email.py`:

```python
"""Email pusher for Morning News fallback notifications.

Uses SMTP SSL to send HTML-formatted email messages as a fallback push channel
when Server酱 is unavailable or rate-limited.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from morning_news.models import Message


class EmailPusher:
    """Push notifications via email (SMTP SSL).

    Args:
        config: Dict with 'smtp_host', 'smtp_port', 'from', 'password', 'to'.
    """

    def __init__(self, config: dict):
        """Initialize email pusher with SMTP configuration.

        Args:
            config: SMTP configuration dict.
        """
        self.smtp_host = config.get("smtp_host", "")
        self.smtp_port = config.get("smtp_port", 465)
        self.from_addr = config.get("from", "")
        self.password = config.get("password", "")
        self.to_addr = config.get("to", "")

    def push(self, message: Message) -> bool:
        """Push a message via email.

        Args:
            message: Message to push.

        Returns:
            True if email sent successfully, False if send failed or config is empty.
        """
        if not self.smtp_host or not self.from_addr or not self.to_addr:
            return False

        try:
            msg = self._create_email(message)

            with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port) as smtp:
                smtp.login(self.from_addr, self.password)
                smtp.sendmail(self.from_addr, self.to_addr, msg.as_string())

            return True

        except Exception:
            return False

    def _create_email(self, message: Message) -> MIMEMultipart:
        """Create a MIME email object from a Message.

        Args:
            message: Message to convert to email format.

        Returns:
            MIMEMultipart email object with HTML content.
        """
        email_msg = MIMEMultipart("alternative")
        email_msg["Subject"] = f"Morning News | {message.title}"
        email_msg["From"] = self.from_addr
        email_msg["To"] = self.to_addr

        # Plain text version
        text_part = MIMEText(message.content, "plain", "utf-8")

        # HTML version with basic styling
        html_content = f"""
<html>
<head><style>
body {{ font-family: sans-serif; padding: 20px; }}
.source {{ color: #666; font-size: 12px; }}
.content {{ white-space: pre-wrap; }}
</style></head>
<body>
<p class="source">来源: {message.source} | 级别: {message.level}</p>
<h2>{message.title}</h2>
<div class="content">{message.content}</div>
</body>
</html>
"""
        html_part = MIMEText(html_content, "html", "utf-8")

        email_msg.attach(text_part)
        email_msg.attach(html_part)

        return email_msg
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_email.py -v
```

Expected: All 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add morning_news/pusher/email.py tests/test_email.py
git commit -m "feat: add email pusher with SMTP SSL and HTML formatting"
```

---

### Task 9: Push Manager

**Files:**
- Create: `morning_news/pusher/manager.py`
- Create: `tests/test_push_manager.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_push_manager.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_push_manager.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'morning_news.pusher.manager'"

- [ ] **Step 3: Write PushManager implementation**

Create `morning_news/pusher/manager.py`:

```python
"""Push manager for Morning News - handles priority routing and fallback.

Strategy:
- urgent messages: always try Server酱 first, fallback to email
- daily messages: check Server酱 daily limit first; if limit reached, go straight to email
- All push attempts are logged to the database
"""

from dataclasses import dataclass
from morning_news.models import Message
from morning_news.pusher.serverchan import ServerChanPusher
from morning_news.pusher.email import EmailPusher


@dataclass
class PushResult:
    """Result of a push attempt.

    Args:
        channel: Which channel was used ('serverchan' or 'email').
        success: Whether the push succeeded.
        message_title: Title of the pushed message.
    """

    channel: str
    success: bool
    message_title: str = ""


class PushManager:
    """Orchestrate message pushing with priority and fallback logic.

    Args:
        serverchan_config: Config dict for Server酱 pusher.
        email_config: Config dict for email pusher.
        db: Database instance for push logging and limit checking.
    """

    def __init__(self, serverchan_config: dict, email_config: dict, db):
        """Initialize PushManager with both push channels.

        Args:
            serverchan_config: Server酱 config (sendkey, daily_limit).
            email_config: SMTP config (host, port, from, password, to).
            db: Database instance for logging and limit tracking.
        """
        self.serverchan = ServerChanPusher(serverchan_config)
        self.email = EmailPusher(email_config)
        self.db = db

    def push(self, message: Message) -> PushResult:
        """Push a message using the appropriate channel based on priority.

        For urgent messages:
        1. Try Server酱 (ignores daily limit)
        2. If Server酱 fails, fallback to email

        For daily messages:
        1. Check Server酱 daily limit
        2. If limit not reached, try Server酱
        3. If limit reached or Server酱 fails, try email

        Args:
            message: Message to push.

        Returns:
            PushResult indicating which channel was used and whether it succeeded.
        """
        if message.level == "urgent":
            return self._push_urgent(message)
        else:
            return self._push_daily(message)

    def _push_urgent(self, message: Message) -> PushResult:
        """Push an urgent message - bypasses daily limit, tries Server酱 first.

        Args:
            message: Urgent message to push.

        Returns:
            PushResult with the channel that succeeded (or failed).
        """
        # Try Server酱 first (urgent messages bypass limit)
        success = self.serverchan.push(message)
        self.db.save_push_log(
            channel="serverchan",
            level=message.level,
            source=message.source,
            title=message.title,
            content=message.content,
            success=success
        )

        if success:
            return PushResult(channel="serverchan", success=True, message_title=message.title)

        # Fallback to email
        success = self.email.push(message)
        self.db.save_push_log(
            channel="email",
            level=message.level,
            source=message.source,
            title=message.title,
            content=message.content,
            success=success
        )

        if success:
            return PushResult(channel="email", success=True, message_title=message.title)

        return PushResult(channel="none", success=False, message_title=message.title)

    def _push_daily(self, message: Message) -> PushResult:
        """Push a daily message - respects Server酱 daily limit.

        Args:
            message: Daily message to push.

        Returns:
            PushResult with the channel that succeeded (or failed).
        """
        # Check Server酱 daily limit
        push_count = self.db.get_push_count_today(channel="serverchan")

        if push_count >= self.serverchan.daily_limit:
            # Limit reached, go straight to email
            success = self.email.push(message)
            self.db.save_push_log(
                channel="email",
                level=message.level,
                source=message.source,
                title=message.title,
                content=message.content,
                success=success
            )
            if success:
                return PushResult(channel="email", success=True, message_title=message.title)
            return PushResult(channel="none", success=False, message_title=message.title)

        # Limit not reached, try Server酱
        success = self.serverchan.push(message)
        self.db.save_push_log(
            channel="serverchan",
            level=message.level,
            source=message.source,
            title=message.title,
            content=message.content,
            success=success
        )

        if success:
            return PushResult(channel="serverchan", success=True, message_title=message.title)

        # Server酱 failed, fallback to email
        success = self.email.push(message)
        self.db.save_push_log(
            channel="email",
            level=message.level,
            source=message.source,
            title=message.title,
            content=message.content,
            success=success
        )

        if success:
            return PushResult(channel="email", success=True, message_title=message.title)

        return PushResult(channel="none", success=False, message_title=message.title)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_push_manager.py -v
```

Expected: All 9 tests PASS

- [ ] **Step 5: Commit**

```bash
git add morning_news/pusher/manager.py tests/test_push_manager.py
git commit -m "feat: add push manager with priority routing, daily limit, and fallback logic"
```