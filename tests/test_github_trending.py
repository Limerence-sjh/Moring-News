"""Tests for GitHub Trending plugin."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import date
from morning_news.plugins.github_trending import GithubTrendingPlugin
from morning_news.models import PluginResult


MOCK_HTML = """
<html><body>
<article class="Box-row">
  <h2 class="h3 lh-condensed">
    <a href="/owner/repo-awesome">
      <span class="text-normal">owner / </span>repo-awesome
    </a>
  </h2>
  <p class="col-9 color-fg-muted my-1 pr-4">
    An awesome project for doing awesome things
  </p>
  <span itemprop="programmingLanguage">Python</span>
  <a class="Link--muted d-inline-block mr-3" href="/owner/repo-awesome/stargazers">
    1,234
  </a>
  <span class="d-inline-block float-sm-right">
    256 stars today
  </span>
</article>
<article class="Box-row">
  <h2 class="h3 lh-condensed">
    <a href="/user/mini-tool">
      <span class="text-normal">user / </span>mini-tool
    </a>
  </h2>
  <p class="col-9 color-fg-muted my-1 pr-4">
    A small handy tool
  </p>
  <span itemprop="programmingLanguage">Rust</span>
  <a class="Link--muted d-inline-block mr-3" href="/user/mini-tool/stargazers">
    890
  </a>
  <span class="d-inline-block float-sm-right">
    78 stars today
  </span>
</article>
<article class="Box-row">
  <h2 class="h3 lh-condensed">
    <a href="/org/no-lang-project">
      <span class="text-normal">org / </span>no-lang-project
    </a>
  </h2>
  <p class="col-9 color-fg-muted my-1 pr-4">
    Project without a language tag
  </p>
  <a class="Link--muted d-inline-block mr-3" href="/org/no-lang-project/stargazers">
    456
  </a>
  <span class="d-inline-block float-sm-right">
    32 stars today
  </span>
</article>
</body></html>
"""


class TestGithubTrendingPluginInit:

    def test_plugin_init_defaults(self):
        config = {"enabled": True}
        plugin = GithubTrendingPlugin(config_section=config)
        assert plugin.name == "github_trending"
        assert plugin.schedule_type == "cron"
        assert plugin.cron_expression == "0 18 * * *"
        assert plugin.top_count == 10
        assert plugin.language == ""
        assert plugin.since == "daily"

    def test_plugin_init_with_config(self):
        config = {
            "enabled": True,
            "top_count": 5,
            "language": "python",
            "since": "weekly"
        }
        plugin = GithubTrendingPlugin(config_section=config)
        assert plugin.top_count == 5
        assert plugin.language == "python"
        assert plugin.since == "weekly"

    def test_plugin_enabled_from_config(self):
        plugin_enabled = GithubTrendingPlugin(config_section={"enabled": True})
        plugin_disabled = GithubTrendingPlugin(config_section={"enabled": False})
        assert plugin_enabled.enabled is True
        assert plugin_disabled.enabled is False


class TestGithubTrendingPluginRun:

    @patch("morning_news.plugins.github_trending.requests.get")
    def test_run_returns_daily_message(self, mock_get, db):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = MOCK_HTML
        mock_get.return_value = mock_response

        plugin = GithubTrendingPlugin(config_section={"enabled": True, "top_count": 10})
        result = plugin.run(db)

        assert result.has_messages is True
        assert result.messages[0].level == "daily"
        assert result.messages[0].title == "GitHub Trending"
        assert result.messages[0].source == "github_trending"

    @patch("morning_news.plugins.github_trending.requests.get")
    def test_parse_extract_repo_info(self, mock_get, db):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = MOCK_HTML
        mock_get.return_value = mock_response

        plugin = GithubTrendingPlugin(config_section={"enabled": True})
        result = plugin.run(db)

        repos = result.data["repos"]
        assert len(repos) == 3
        assert repos[0]["name"] == "owner/repo-awesome"
        assert repos[0]["description"] == "An awesome project for doing awesome things"
        assert repos[0]["language"] == "Python"
        assert repos[1]["name"] == "user/mini-tool"
        assert repos[1]["language"] == "Rust"
        assert repos[2]["name"] == "org/no-lang-project"
        assert repos[2]["language"] == ""

    @patch("morning_news.plugins.github_trending.requests.get")
    def test_top_count_limits_repos(self, mock_get, db):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = MOCK_HTML
        mock_get.return_value = mock_response

        plugin = GithubTrendingPlugin(config_section={"enabled": True, "top_count": 2})
        result = plugin.run(db)

        repos = result.data["repos"]
        assert len(repos) == 2
        assert repos[0]["name"] == "owner/repo-awesome"
        assert repos[1]["name"] == "user/mini-tool"

    @patch("morning_news.plugins.github_trending.requests.get")
    def test_api_error_returns_empty_result(self, mock_get, db):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = ""
        mock_get.return_value = mock_response

        plugin = GithubTrendingPlugin(config_section={"enabled": True})
        result = plugin.run(db)

        assert not result.has_messages
        assert result.data.get("error") == "fetch_failed"

    @patch("morning_news.plugins.github_trending.requests.get")
    def test_network_error_returns_empty_result(self, mock_get, db):
        mock_get.side_effect = Exception("Network error")

        plugin = GithubTrendingPlugin(config_section={"enabled": True})
        result = plugin.run(db)

        assert not result.has_messages

    @patch("morning_news.plugins.github_trending.requests.get")
    def test_db_save_called(self, mock_get, db):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = MOCK_HTML
        mock_get.return_value = mock_response

        plugin = GithubTrendingPlugin(config_section={"enabled": True})
        plugin.run(db)

        saved = db.get_daily_data(source="github_trending", date=date.today().isoformat())
        assert saved is not None
        assert "repos" in saved
        assert len(saved["repos"]) == 3

    @patch("morning_news.plugins.github_trending.requests.get")
    def test_message_format_list_style(self, mock_get, db):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = MOCK_HTML
        mock_get.return_value = mock_response

        plugin = GithubTrendingPlugin(config_section={"enabled": True, "top_count": 3})
        result = plugin.run(db)

        content = result.messages[0].content
        lines = content.strip().split("\n")
        assert len(lines) == 3
        assert lines[0].startswith("1.")
        assert lines[1].startswith("2.")
        assert lines[2].startswith("3.")
        assert "owner/repo-awesome" in lines[0]
        assert "Python" in lines[0]


class TestGithubTrendingBuildUrl:

    def test_url_no_language(self):
        plugin = GithubTrendingPlugin(config_section={"enabled": True, "language": "", "since": "daily"})
        url = plugin._build_url()
        assert url == "https://github.com/trending?since=daily"

    def test_url_with_language(self):
        plugin = GithubTrendingPlugin(config_section={"enabled": True, "language": "python", "since": "weekly"})
        url = plugin._build_url()
        assert url == "https://github.com/trending/python?since=weekly"

    def test_url_monthly_since(self):
        plugin = GithubTrendingPlugin(config_section={"enabled": True, "language": "", "since": "monthly"})
        url = plugin._build_url()
        assert url == "https://github.com/trending?since=monthly"