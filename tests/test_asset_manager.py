import json
import os
import tempfile
from unittest.mock import patch, MagicMock
from asset_mgr.manager import AssetManager


def _mock_urlopen_search(response_body):
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(response_body).encode("utf-8")
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


def test_search_local_and_github():
    with tempfile.TemporaryDirectory() as tmpdir:
        mgr = AssetManager(tmpdir)
        mgr.store.register_asset("hair", "blue_twintail", ["blue", "twintail"], "", "MIT")

        mock_github = _mock_urlopen_search({
            "items": [{
                "full_name": "user/mmd-hair",
                "description": "MMD hair pack",
                "html_url": "https://github.com/user/mmd-hair",
                "stargazers_count": 10,
                "license": {"spdx_id": "MIT"},
                "topics": ["mmd"],
            }]
        })

        with patch("urllib.request.urlopen", return_value=mock_github):
            result = mgr.search("twintail")

        assert result["success"] is True
        assert len(result["results"]) == 2  # 1 local + 1 github
        assert result["results"][0]["source"] == "local"
        assert result["results"][1]["source"] == "github"


def test_search_empty_query():
    with tempfile.TemporaryDirectory() as tmpdir:
        mgr = AssetManager(tmpdir)
        result = mgr.search("")
        assert result["success"] is False


def test_handle_intent_search():
    with tempfile.TemporaryDirectory() as tmpdir:
        mgr = AssetManager(tmpdir)
        with patch("urllib.request.urlopen", return_value=_mock_urlopen_search({"items": []})):
            result = mgr.handle_intent("search", {"query": "test"})
        assert result["success"] is True


def test_handle_intent_list():
    with tempfile.TemporaryDirectory() as tmpdir:
        mgr = AssetManager(tmpdir)
        mgr.store.register_asset("hair", "test", ["test"], "", "")
        result = mgr.handle_intent("list", {"category": "hair"})
        assert result["success"] is True
        assert len(result["results"]) == 1


def test_handle_intent_remove():
    with tempfile.TemporaryDirectory() as tmpdir:
        mgr = AssetManager(tmpdir)
        mgr.store.register_asset("hair", "temp", ["temp"], "", "")
        result = mgr.handle_intent("remove", {"category": "hair", "name": "temp"})
        assert result["success"] is True
        assert len(mgr.store.search("temp")) == 0


def test_import_local_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        mgr = AssetManager(tmpdir)
        # Create a fake file to import
        fake_file = os.path.join(tmpdir, "test_model.blend")
        with open(fake_file, "w") as f:
            f.write("fake blend data")

        result = mgr.import_local(fake_file, "imported_hair", "hair", ["test", "imported"])
        assert result["success"] is True
        assert len(mgr.store.search("imported")) == 1


def test_handle_intent_unknown():
    with tempfile.TemporaryDirectory() as tmpdir:
        mgr = AssetManager(tmpdir)
        result = mgr.handle_intent("unknown_action", {})
        assert result["success"] is False
