# asset_mgr/manager.py
"""
Asset Manager: orchestrates local storage + remote search.
Handles the "asset" intent type from the AI.
"""
import os
import json
import zipfile
import tempfile
import urllib.request
from typing import Optional
from .local_store import LocalAssetStore
from .sources.github_source import GitHubAssetSource


class AssetManager:
    """
    High-level asset management.

    Handles three actions from AI intents:
    - search: Search local + GitHub for assets
    - download: Download and install an asset from a URL
    - import_local: Import a local file into the asset library
    """

    def __init__(self, library_path: str, github_token: Optional[str] = None):
        self.store = LocalAssetStore(library_path)
        self.github = GitHubAssetSource(token=github_token)

    def handle_intent(self, action: str, params: dict) -> dict:
        """
        Handle an asset intent from the AI.
        This is the entry point used by IntentRouter.
        """
        if action == "search":
            return self.search(params.get("query", ""), params.get("category", ""))
        elif action == "download":
            return self.download(
                url=params.get("url", ""),
                name=params.get("name", ""),
                category=params.get("category", "hair"),
                tags=params.get("tags", []),
                license_type=params.get("license", "unknown"),
            )
        elif action == "import_local":
            return self.import_local(
                filepath=params.get("filepath", ""),
                name=params.get("name", ""),
                category=params.get("category", "hair"),
                tags=params.get("tags", []),
            )
        elif action == "list":
            return self.list_assets(params.get("category", ""))
        elif action == "remove":
            return self.remove(params.get("category", ""), params.get("name", ""))
        else:
            return {"success": False, "error": f"未知的资产操作: {action}"}

    def search(self, query: str, category: str = "") -> dict:
        """
        Search for assets locally first, then on GitHub.
        Returns combined results with source indicated.
        """
        if not query:
            return {"success": False, "error": "请提供搜索关键词"}

        results = []

        # Search local first
        local_results = self.store.search(query)
        if category:
            local_results = [r for r in local_results if r.get("category") == category]
        for r in local_results:
            r["source"] = "local"
            results.append(r)

        # Search GitHub
        github_results = self.github.search(query, max_results=5)
        for r in github_results:
            r["source"] = "github"
            results.append(r)

        if not results:
            recommendations = self.github.format_recommendations(query)
            return {
                "success": True,
                "results": [],
                "message": f"未找到与「{query}」相关的资产。\n{recommendations}",
            }

        return {
            "success": True,
            "results": results,
            "message": f"找到 {len(local_results)} 个本地资产和 {len(github_results)} 个 GitHub 仓库",
        }

    def download(self, url: str, name: str, category: str, tags: list[str], license_type: str) -> dict:
        """
        Download an asset from a URL and register it in the local library.
        Supports .zip, .blend, .pmx files.
        """
        if not url:
            return {"success": False, "error": "请提供下载链接(url)"}
        if not name:
            # Extract name from URL
            name = url.split("/")[-1].split(".")[0].replace(" ", "_")

        asset_dir = self.store.get_asset_path(category, name)
        os.makedirs(asset_dir, exist_ok=True)

        try:
            # Download file
            req = urllib.request.Request(url, headers={"User-Agent": "AIMoeMaker/0.1"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                content = resp.read()

            # Determine file type and handle accordingly
            if url.endswith(".zip") or url.endswith(".tar.gz"):
                # Extract zip
                zip_path = os.path.join(asset_dir, "download.zip")
                with open(zip_path, "wb") as f:
                    f.write(content)

                try:
                    with zipfile.ZipFile(zip_path, "r") as zf:
                        zf.extractall(asset_dir)
                    os.remove(zip_path)
                except zipfile.BadZipFile:
                    return {"success": False, "error": "下载的文件不是有效的 ZIP 压缩包"}
            else:
                # Save single file
                filename = url.split("/")[-1]
                filepath = os.path.join(asset_dir, filename)
                with open(filepath, "wb") as f:
                    f.write(content)

            # Register in index
            self.store.register_asset(
                category=category,
                name=name,
                tags=tags,
                source_url=url,
                license_type=license_type,
            )

            return {
                "success": True,
                "message": f"资产已下载并安装: {name} ({category})",
                "path": asset_dir,
            }

        except urllib.error.URLError as e:
            return {"success": False, "error": f"下载失败: {e.reason}"}
        except Exception as e:
            return {"success": False, "error": f"下载出错: {str(e)}"}

    def import_local(self, filepath: str, name: str, category: str, tags: list[str]) -> dict:
        """
        Import a local file into the asset library.
        Copies the file to the library directory and registers it.
        """
        if not filepath or not os.path.exists(filepath):
            return {"success": False, "error": f"文件不存在: {filepath}"}
        if not name:
            name = os.path.splitext(os.path.basename(filepath))[0]

        import shutil
        asset_dir = self.store.get_asset_path(category, name)
        os.makedirs(asset_dir, exist_ok=True)

        dest = os.path.join(asset_dir, os.path.basename(filepath))
        shutil.copy2(filepath, dest)

        self.store.register_asset(
            category=category,
            name=name,
            tags=tags,
            source_url=f"local://{filepath}",
            license_type="local",
        )

        return {
            "success": True,
            "message": f"已导入资产: {name} ({category})",
            "path": asset_dir,
        }

    def list_assets(self, category: str = "") -> dict:
        """List all assets, optionally filtered by category."""
        if category:
            assets = self.store.list_category(category)
        else:
            assets = self.store.get_all_assets()

        if not assets:
            return {"success": True, "results": [], "message": "本地资产库为空"}

        return {
            "success": True,
            "results": assets,
            "message": f"共 {len(assets)} 个本地资产",
        }

    def remove(self, category: str, name: str) -> dict:
        """Remove an asset from the library index."""
        if not category or not name:
            return {"success": False, "error": "请指定分类(category)和名称(name)"}
        self.store.remove_asset(category, name)
        return {"success": True, "message": f"已移除资产: {name}"}
