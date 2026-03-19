"""
Scene inspection commands: let AI read the Blender scene on demand.
"""
from .base import BaseCommand


class InspectScene(BaseCommand):
    action = "inspect_scene"

    def execute(self, params: dict, context: dict) -> dict:
        if not context.get("bpy_available", False):
            return {"success": False, "error": "需要在 Blender 环境中运行"}
        from ..blender_ops.scene_inspector import get_scene_snapshot
        snapshot = get_scene_snapshot()
        # Format as readable text for AI context
        snapshot["message"] = _format_snapshot(snapshot)
        return snapshot


class InspectCollection(BaseCommand):
    action = "inspect_collection"

    def execute(self, params: dict, context: dict) -> dict:
        if not context.get("bpy_available", False):
            return {"success": False, "error": "需要在 Blender 环境中运行"}
        name = params.get("name", "")
        if not name:
            return {"success": False, "error": "请指定集合名称 (name)"}
        from ..blender_ops.scene_inspector import inspect_collection
        result = inspect_collection(name)
        if result["success"]:
            result["message"] = _format_collection(result)
        return result


class InspectObject(BaseCommand):
    action = "inspect_object"

    def execute(self, params: dict, context: dict) -> dict:
        if not context.get("bpy_available", False):
            return {"success": False, "error": "需要在 Blender 环境中运行"}
        name = params.get("name", "")
        if not name:
            return {"success": False, "error": "请指定对象名称 (name)"}
        from ..blender_ops.scene_inspector import inspect_object
        result = inspect_object(name)
        if result["success"]:
            result["message"] = _format_object(result)
        return result


# ---------------------------------------------------------------------------
# Formatters — turn structured dicts into readable text for AI
# ---------------------------------------------------------------------------

def _format_snapshot(snap: dict) -> str:
    lines = [f"场景: {snap.get('scene_name', '?')}, 共 {snap.get('total_objects', 0)} 个对象"]
    tc = snap.get("type_counts", {})
    if tc:
        lines.append("类型分布: " + ", ".join(f"{k} {v}" for k, v in tc.items()))
    mats = snap.get("materials_in_use", [])
    if mats:
        lines.append(f"使用中的材质({len(mats)}): " + ", ".join(mats[:20]))

    cols = snap.get("collections")
    if cols:
        lines.append("集合层级:")
        _format_col_tree(cols, lines, indent=1)

    active = snap.get("active_object")
    if active:
        lines.append(f"当前选中: {active.get('name', '?')} ({active.get('type_zh', '?')})")
    return "\n".join(lines)


def _format_col_tree(col: dict, lines: list, indent: int):
    prefix = "  " * indent
    obj_names = col.get("objects", [])
    suffix = f" [{len(obj_names)}个对象]" if obj_names else ""
    lines.append(f"{prefix}📁 {col['name']}{suffix}")
    for name in obj_names:
        lines.append(f"{prefix}  · {name}")
    for child in col.get("children", []):
        _format_col_tree(child, lines, indent + 1)


def _format_collection(result: dict) -> str:
    lines = [f"集合 '{result['collection']}': {result['object_count']} 个对象"]
    children = result.get("child_collections", [])
    if children:
        lines.append(f"子集合: {', '.join(children)}")
    for obj in result.get("objects", []):
        desc = f"  · {obj['name']} [{obj.get('type_zh', obj.get('type', '?'))}]"
        if "vertices" in obj:
            desc += f" {obj['vertices']}顶点/{obj['faces']}面"
        if "bone_count" in obj:
            desc += f" {obj['bone_count']}骨骼"
        if obj.get("materials"):
            desc += f" 材质:{','.join(obj['materials'])}"
        lines.append(desc)
    return "\n".join(lines)


def _format_object(result: dict) -> str:
    lines = [f"对象: {result['name']} ({result.get('type_zh', result.get('type', '?'))})"]
    if "vertices" in result:
        lines.append(f"  网格: {result['vertices']}顶点, {result['faces']}面, {result['edges']}边")
    if "bone_count" in result:
        lines.append(f"  骨骼数: {result['bone_count']}")
    if result.get("materials"):
        lines.append(f"  材质: {', '.join(result['materials'])}")
    if result.get("shape_keys"):
        lines.append(f"  形态键({result.get('shape_key_count', 0)}): {', '.join(result['shape_keys'][:15])}")
    if "vertex_group_count" in result:
        lines.append(f"  顶点组: {result['vertex_group_count']}个")
        if result.get("vertex_groups"):
            lines.append(f"    {', '.join(result['vertex_groups'][:20])}")
    if result.get("modifiers"):
        mods = [f"{m['name']}({m['type']})" for m in result["modifiers"]]
        lines.append(f"  修改器: {', '.join(mods)}")
    if result.get("rigid_body"):
        rb = result["rigid_body"]
        lines.append(f"  刚体: 类型={rb['type']}, 质量={rb['mass']}")
    if result.get("custom_properties"):
        props = [f"{k}={v}" for k, v in result["custom_properties"].items()]
        lines.append(f"  自定义属性: {', '.join(props[:10])}")
    if result.get("parent"):
        lines.append(f"  父级: {result['parent']}")
    if result.get("children"):
        lines.append(f"  子级: {', '.join(result['children'])}")
    loc = result.get("location", [])
    if loc:
        lines.append(f"  位置: ({loc[0]}, {loc[1]}, {loc[2]})")
    return "\n".join(lines)


SCENE_COMMANDS = [InspectScene, InspectCollection, InspectObject]
