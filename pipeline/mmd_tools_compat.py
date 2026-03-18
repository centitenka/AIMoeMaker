# pipeline/mmd_tools_compat.py
"""
mmd_tools compatibility layer.
Detects mmd_tools installation, provides version info, and wraps common operations.

mmd_tools (blender_mmd_tools) is the community Blender addon for MMD/PMX support.
Repository: https://github.com/UuuNyaa/blender_mmd_tools (or its successors)
"""

_mmd_tools = None
_mmd_tools_checked = False


def is_mmd_tools_available() -> bool:
    """Check if mmd_tools is installed and enabled in Blender."""
    global _mmd_tools, _mmd_tools_checked
    if _mmd_tools_checked:
        return _mmd_tools is not None

    _mmd_tools_checked = True
    try:
        import mmd_tools
        _mmd_tools = mmd_tools
        return True
    except ImportError:
        pass

    # Try alternate import paths (some forks use different module names)
    for module_name in ["mmd_tools", "mmd_tools_local", "blender_mmd_tools"]:
        try:
            import importlib
            _mmd_tools = importlib.import_module(module_name)
            return True
        except ImportError:
            continue

    _mmd_tools = None
    return False


def get_mmd_tools():
    """Get the mmd_tools module. Returns None if not available."""
    if not is_mmd_tools_available():
        return None
    return _mmd_tools


def get_mmd_tools_version() -> str:
    """Get mmd_tools version string, or 'not installed'."""
    mod = get_mmd_tools()
    if mod is None:
        return "not installed"
    return getattr(mod, "__version__", getattr(mod, "bl_info", {}).get("version", "unknown"))


def get_install_guidance() -> str:
    """Return user-friendly installation guidance in Chinese."""
    return """mmd_tools 未安装。请按以下步骤安装：

1. 访问 https://github.com/UuuNyaa/blender_mmd_tools/releases
2. 下载最新版本的 .zip 文件
3. 在 Blender 中：编辑 → 偏好设置 → 插件 → 安装
4. 选择下载的 .zip 文件
5. 勾选启用 "MMD Tools"
6. 重启 Blender

安装完成后，AIMoeMaker 将自动检测并启用 PMX 导出功能。"""


def check_mmd_tools_or_report() -> dict:
    """
    Check mmd_tools availability and return a status dict.
    Suitable for use in command execute() methods.
    """
    if is_mmd_tools_available():
        return {
            "available": True,
            "version": get_mmd_tools_version(),
        }
    return {
        "available": False,
        "error": "mmd_tools 未安装",
        "guidance": get_install_guidance(),
    }


# --- mmd_tools API wrappers ---
# These wrap mmd_tools operations to isolate version differences

def create_mmd_root(armature_obj) -> bool:
    """
    Convert a standard Blender armature to an MMD model root.
    This sets up the mmd_tools data structures on the armature.
    """
    mod = get_mmd_tools()
    if mod is None:
        return False

    try:
        # mmd_tools uses an operator to create the MMD model structure
        import bpy
        bpy.context.view_layer.objects.active = armature_obj

        # Check if already has MMD root
        if hasattr(armature_obj, 'mmd_type') and armature_obj.mmd_type == 'ROOT':
            return True

        # Try to use mmd_tools operator
        if hasattr(bpy.ops, 'mmd_tools') and hasattr(bpy.ops.mmd_tools, 'convert_to_mmd_model'):
            bpy.ops.mmd_tools.convert_to_mmd_model()
            return True

        return False
    except Exception:
        return False


def export_pmx_file(filepath: str, armature_obj=None) -> dict:
    """
    Export the current scene/model to PMX format using mmd_tools.

    Args:
        filepath: Output .pmx file path
        armature_obj: Optional specific armature to export

    Returns:
        {"success": bool, "error": str (if failed)}
    """
    mod = get_mmd_tools()
    if mod is None:
        return {"success": False, "error": "mmd_tools 未安装，无法导出 PMX"}

    try:
        import bpy

        # Select the armature/model to export
        if armature_obj:
            bpy.ops.object.select_all(action='DESELECT')
            armature_obj.select_set(True)
            bpy.context.view_layer.objects.active = armature_obj

        # Use mmd_tools export operator
        if hasattr(bpy.ops, 'mmd_tools') and hasattr(bpy.ops.mmd_tools, 'export_pmx'):
            bpy.ops.mmd_tools.export_pmx(filepath=filepath)
            return {"success": True, "message": f"已导出 PMX: {filepath}"}

        # Fallback: try direct export function
        if hasattr(mod, 'operators') and hasattr(mod.operators, 'fileio'):
            # Some versions use this path
            pass

        return {"success": False, "error": "mmd_tools 版本不兼容，找不到导出功能"}

    except Exception as e:
        return {"success": False, "error": f"PMX 导出失败: {str(e)}"}
