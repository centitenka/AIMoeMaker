import json
from unittest.mock import patch, MagicMock
from asset_mgr.sources.github_source import GitHubAssetSource


def _mock_urlopen(response_body):
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(response_body).encode("utf-8")
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    mock_resp.status = 200
    return mock_resp


def test_search_returns_results():
    source = GitHubAssetSource()
    mock_response = _mock_urlopen({
        "items": [
            {
                "full_name": "user/mmd-hair-pack",
                "description": "MMD hair models collection - twintail, ponytail, etc.",
                "html_url": "https://github.com/user/mmd-hair-pack",
                "stargazers_count": 42,
                "license": {"spdx_id": "MIT"},
                "topics": ["mmd", "pmx", "hair"],
            },
            {
                "full_name": "user2/miku-assets",
                "description": "初音ミク MMD model parts",
                "html_url": "https://github.com/user2/miku-assets",
                "stargazers_count": 100,
                "license": {"spdx_id": "CC-BY-4.0"},
                "topics": ["mmd", "vocaloid"],
            }
        ]
    })

    with patch("urllib.request.urlopen", return_value=mock_response):
        results = source.search("初音 hair")

    assert len(results) == 2
    assert results[0]["name"] == "mmd-hair-pack"
    assert results[0]["license"] == "MIT"
    assert results[1]["stars"] == 100


def test_search_network_error():
    source = GitHubAssetSource()
    with patch("urllib.request.urlopen", side_effect=Exception("Network error")):
        results = source.search("test query")
    assert results == []


def test_search_empty_results():
    source = GitHubAssetSource()
    mock_response = _mock_urlopen({"items": []})
    with patch("urllib.request.urlopen", return_value=mock_response):
        results = source.search("nonexistent asset xyz123")
    assert results == []


def test_get_download_url():
    source = GitHubAssetSource()
    url = source.get_download_url("user/repo", "main")
    assert "github.com" in url
    assert "user/repo" in url
    assert "archive" in url


def test_format_search_recommendations():
    source = GitHubAssetSource()
    recs = source.format_recommendations("初音未来 头发")
    assert isinstance(recs, str)
    assert "初音" in recs or "搜索" in recs
