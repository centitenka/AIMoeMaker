# asset_mgr/local_store.py
"""
Local asset library storage.
Manages a folder-based asset library with a JSON index for fast search.

Structure:
  asset_library/
    index.json
    hair/
      twintail_01/
        model.blend
        meta.json
        thumbnail.png
    clothing/
    accessory/
    body/
    eyes/
"""
import json
import os
import time
from typing import Optional

CATEGORIES = ["hair", "clothing", "accessory", "body", "eyes"]
SCHEMA_VERSION = 1


class LocalAssetStore:
    """Manages the local asset library."""

    def __init__(self, base_path: str):
        self.base_path = base_path
        self._index_path = os.path.join(base_path, "index.json")
        self._index: dict = {"schema_version": SCHEMA_VERSION, "assets": []}
        self._ensure_structure()
        self._load_index()

    def _ensure_structure(self):
        """Create the directory structure if it doesn't exist."""
        os.makedirs(self.base_path, exist_ok=True)
        for cat in CATEGORIES:
            os.makedirs(os.path.join(self.base_path, cat), exist_ok=True)
        if not os.path.exists(self._index_path):
            self._save_index()

    def _load_index(self):
        """Load the asset index from disk."""
        if os.path.exists(self._index_path):
            with open(self._index_path, "r", encoding="utf-8") as f:
                self._index = json.load(f)
        if "assets" not in self._index:
            self._index["assets"] = []

    def _save_index(self):
        """Save the asset index to disk."""
        with open(self._index_path, "w", encoding="utf-8") as f:
            json.dump(self._index, f, ensure_ascii=False, indent=2)

    def register_asset(
        self,
        category: str,
        name: str,
        tags: list[str],
        source_url: str,
        license_type: str,
    ):
        """
        Register an asset in the index.
        The asset files should already be in the correct directory.
        """
        # Remove existing entry with same name+category
        self._index["assets"] = [
            a for a in self._index["assets"]
            if not (a["name"] == name and a["category"] == category)
        ]

        entry = {
            "name": name,
            "category": category,
            "tags": tags,
            "source_url": source_url,
            "license": license_type,
            "path": os.path.join(category, name),
            "registered_at": time.time(),
        }
        self._index["assets"].append(entry)

        # Write meta.json in asset directory
        asset_dir = os.path.join(self.base_path, category, name)
        os.makedirs(asset_dir, exist_ok=True)
        meta_path = os.path.join(asset_dir, "meta.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(entry, f, ensure_ascii=False, indent=2)

        self._save_index()

    def remove_asset(self, category: str, name: str):
        """Remove an asset from the index (does not delete files)."""
        self._index["assets"] = [
            a for a in self._index["assets"]
            if not (a["name"] == name and a["category"] == category)
        ]
        self._save_index()

    def search(self, query: str) -> list[dict]:
        """
        Search assets by query string.
        Matches against name and tags (case-insensitive).
        """
        query_lower = query.lower()
        results = []
        for asset in self._index["assets"]:
            if query_lower in asset["name"].lower():
                results.append(asset)
                continue
            for tag in asset.get("tags", []):
                if query_lower in tag.lower():
                    results.append(asset)
                    break
        return results

    def list_category(self, category: str) -> list[dict]:
        """List all assets in a category."""
        return [a for a in self._index["assets"] if a["category"] == category]

    def get_asset_path(self, category: str, name: str) -> str:
        """Get the full filesystem path for an asset directory."""
        return os.path.join(self.base_path, category, name)

    def get_asset_meta(self, category: str, name: str) -> Optional[dict]:
        """Get metadata for a specific asset."""
        for asset in self._index["assets"]:
            if asset["name"] == name and asset["category"] == category:
                return asset
        return None

    def get_all_assets(self) -> list[dict]:
        """Get all registered assets."""
        return list(self._index["assets"])
