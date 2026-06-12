"""GitHub Trending plugin for Morning News.

Fetches daily trending repositories from GitHub Trending page
and formats them as a daily summary message.
"""

import requests
from bs4 import BeautifulSoup
from datetime import date
from typing import Dict, List, Optional
from morning_news.plugins.base import BasePlugin
from morning_news.models import Message, PluginResult


class GithubTrendingPlugin(BasePlugin):
    """Fetch GitHub trending repositories and format as daily summary.

    Config keys:
        top_count: Number of top repos to include (default 10).
        language: Programming language filter (default "" = all languages).
        since: Time range filter - 'daily', 'weekly', 'monthly' (default 'daily').
    """

    name = "github_trending"
    schedule_type = "cron"
    cron_expression = "0 18 * * *"

    def __init__(self, config_section: dict):
        super().__init__(config_section)
        self.top_count = config_section.get("top_count", 10)
        self.language = config_section.get("language", "")
        self.since = config_section.get("since", "daily")

    def run(self, db) -> PluginResult:
        url = self._build_url()
        html = self._fetch_html(url)
        if html is None:
            return PluginResult(messages=[], data={"error": "fetch_failed"})

        repos = self._parse_repos(html)
        repos = repos[:self.top_count]

        if not repos:
            return PluginResult(messages=[], data={"repos": []})

        today = date.today().isoformat()
        db.save_daily_data(source=self.name, date=today, data={"repos": repos})

        content = self._format_message(repos)
        message = Message(
            title="GitHub Trending",
            content=content,
            level="daily",
            source=self.name
        )

        return PluginResult(messages=[message], data={"repos": repos})

    def _build_url(self) -> str:
        lang_part = self.language if self.language else ""
        if lang_part:
            return f"https://github.com/trending/{lang_part}?since={self.since}"
        return f"https://github.com/trending?since={self.since}"

    def _fetch_html(self, url: str) -> Optional[str]:
        try:
            response = requests.get(url, timeout=15)
            if response.status_code != 200:
                return None
            return response.text
        except Exception:
            return None

    def _parse_repos(self, html: str) -> List[Dict]:
        soup = BeautifulSoup(html, "lxml")
        articles = soup.select("article.Box-row")
        repos = []

        for article in articles:
            repo_name = self._extract_repo_name(article)
            description = self._extract_description(article)
            language = self._extract_language(article)
            stars_today = self._extract_stars_today(article)

            repos.append({
                "name": repo_name,
                "description": description,
                "language": language,
                "stars_today": stars_today,
            })

        return repos

    def _extract_repo_name(self, article) -> str:
        h2 = article.select_one("h2 a")
        if h2 is None:
            return ""
        href = h2.get("href", "")
        return href.strip().lstrip("/")

    def _extract_description(self, article) -> str:
        p = article.select_one("p")
        if p is None:
            return ""
        return p.get_text(strip=True)

    def _extract_language(self, article) -> str:
        lang_elem = article.select_one("[itemprop='programmingLanguage']")
        if lang_elem is None:
            return ""
        return lang_elem.get_text(strip=True)

    def _extract_stars_today(self, article) -> str:
        star_links = article.select("a.Link--muted.d-inline-block.mr-3")
        for link in star_links:
            href = link.get("href", "")
            if "/stargazers" in href:
                return link.get_text(strip=True)
        star_span = article.select_one("span.d-inline-block.float-sm-right")
        if star_span is None:
            return ""
        return star_span.get_text(strip=True)

    def _format_message(self, repos: List[Dict]) -> str:
        lines = []
        for i, repo in enumerate(repos, 1):
            parts = [f"{i}. {repo['name']}"]
            if repo["stars_today"]:
                parts.append(f"⭐ {repo['stars_today']}")
            if repo["language"]:
                parts.append(f"[{repo['language']}]")
            if repo["description"]:
                parts.append(f"- {repo['description']}")
            lines.append(" ".join(parts))
        return "\n".join(lines)