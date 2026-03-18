# asset_mgr/sources/github_source.py
"""
GitHub API search source for MMD assets.
Searches public repositories with open-source licenses.
"""
import json
import urllib.request
import urllib.error
import urllib.parse
from typing import Optional


GITHUB_API_BASE = "https://api.github.com"
GITHUB_SEARCH_URL = f"{GITHUB_API_BASE}/search/repositories"

# Default search qualifiers to narrow results to MMD-related repos
DEFAULT_QUALIFIERS = "topic:mmd OR topic:pmx OR topic:mikumikudance"


class GitHubAssetSource:
    """Search GitHub for open-source MMD asset repositories."""

    def __init__(self, token: Optional[str] = None):
        """
        Args:
            token: Optional GitHub personal access token for higher rate limits.
        """
        self.token = token

    def search(self, query: str, max_results: int = 10) -> list[dict]:
        """
        Search GitHub for MMD asset repositories.

        Args:
            query: User's search query (can be Chinese or English)
            max_results: Maximum results to return

        Returns:
            List of dicts with: name, full_name, description, url, stars, license, topics
        """
        search_query = f"{query} {DEFAULT_QUALIFIERS}"
        params = {
            "q": search_query,
            "sort": "stars",
            "order": "desc",
            "per_page": min(max_results, 30),
        }

        url = f"{GITHUB_SEARCH_URL}?{urllib.parse.urlencode(params)}"
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AIMoeMaker/0.1",
        }
        if self.token:
            headers["Authorization"] = f"token {self.token}"

        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            results = []
            for item in data.get("items", []):
                license_info = item.get("license") or {}
                results.append({
                    "name": item["full_name"].split("/")[-1],
                    "full_name": item["full_name"],
                    "description": item.get("description", ""),
                    "url": item.get("html_url", ""),
                    "stars": item.get("stargazers_count", 0),
                    "license": license_info.get("spdx_id", "unknown"),
                    "topics": item.get("topics", []),
                })
            return results

        except Exception:
            return []

    def get_download_url(self, full_name: str, branch: str = "main") -> str:
        """
        Get the archive download URL for a repository.

        Args:
            full_name: Repository full name (e.g. "user/repo")
            branch: Branch name to download
        """
        return f"https://github.com/{full_name}/archive/refs/heads/{branch}.zip"

    def get_release_assets(self, full_name: str) -> list[dict]:
        """
        Get downloadable assets from the latest release.

        Returns:
            List of dicts with: name, url, size
        """
        url = f"{GITHUB_API_BASE}/repos/{full_name}/releases/latest"
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AIMoeMaker/0.1",
        }
        if self.token:
            headers["Authorization"] = f"token {self.token}"

        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            assets = []
            for asset in data.get("assets", []):
                assets.append({
                    "name": asset["name"],
                    "url": asset["browser_download_url"],
                    "size": asset.get("size", 0),
                })
            return assets

        except Exception:
            return []

    def format_recommendations(self, query: str) -> str:
        """
        Format search recommendations as Chinese text for the user.
        Used when no results are found or as additional guidance.
        """
        keywords = query.split()
        suggestions = [
            f"在 GitHub 上搜索: {query}",
            "推荐搜索关键词:",
        ]
        for kw in keywords:
            suggestions.append(f"  - {kw} MMD model")
            suggestions.append(f"  - {kw} PMX")

        suggestions.extend([
            "",
            "也可以尝试以下网站手动搜索:",
            "  - Bowlroll: https://bowlroll.net",
            "  - DeviantArt: https://www.deviantart.com (搜索 'MMD model')",
            "  - Niconi立体: https://3d.nicovideo.jp",
        ])

        return "\n".join(suggestions)
