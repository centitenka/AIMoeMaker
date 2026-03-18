import json
import os
import tempfile
from asset_mgr.local_store import LocalAssetStore


def test_init_creates_structure():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = LocalAssetStore(tmpdir)
        assert os.path.exists(os.path.join(tmpdir, "index.json"))
        assert os.path.isdir(os.path.join(tmpdir, "hair"))
        assert os.path.isdir(os.path.join(tmpdir, "clothing"))
        assert os.path.isdir(os.path.join(tmpdir, "accessory"))
        assert os.path.isdir(os.path.join(tmpdir, "body"))


def test_register_asset():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = LocalAssetStore(tmpdir)
        # Create a fake asset file
        asset_dir = os.path.join(tmpdir, "hair", "twintail_blue")
        os.makedirs(asset_dir)
        with open(os.path.join(asset_dir, "model.blend"), "w") as f:
            f.write("fake blend")

        store.register_asset(
            category="hair",
            name="twintail_blue",
            tags=["twintail", "blue", "初音"],
            source_url="https://github.com/example/mmd-assets",
            license_type="CC-BY-4.0",
        )

        # Should appear in index
        assets = store.search("twintail")
        assert len(assets) == 1
        assert assets[0]["name"] == "twintail_blue"


def test_search_by_tag():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = LocalAssetStore(tmpdir)
        store.register_asset("hair", "ponytail_red", ["ponytail", "red"], "", "")
        store.register_asset("hair", "twintail_blue", ["twintail", "blue", "初音"], "", "")
        store.register_asset("clothing", "gothic_dress", ["gothic", "dress", "黑色"], "", "")

        assert len(store.search("blue")) == 1
        assert len(store.search("初音")) == 1
        assert len(store.search("gothic")) == 1
        assert len(store.search("nonexistent")) == 0


def test_search_by_category():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = LocalAssetStore(tmpdir)
        store.register_asset("hair", "ponytail", ["ponytail"], "", "")
        store.register_asset("clothing", "dress", ["dress"], "", "")

        assert len(store.list_category("hair")) == 1
        assert len(store.list_category("clothing")) == 1
        assert len(store.list_category("accessory")) == 0


def test_remove_asset():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = LocalAssetStore(tmpdir)
        store.register_asset("hair", "temp_hair", ["temp"], "", "")
        assert len(store.search("temp")) == 1

        store.remove_asset("hair", "temp_hair")
        assert len(store.search("temp")) == 0


def test_get_asset_path():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = LocalAssetStore(tmpdir)
        path = store.get_asset_path("hair", "twintail_01")
        assert "hair" in path
        assert "twintail_01" in path


def test_persistence():
    with tempfile.TemporaryDirectory() as tmpdir:
        store1 = LocalAssetStore(tmpdir)
        store1.register_asset("hair", "test_hair", ["test"], "", "MIT")

        # Reload from disk
        store2 = LocalAssetStore(tmpdir)
        assets = store2.search("test")
        assert len(assets) == 1
        assert assets[0]["license"] == "MIT"
