"""
Blender scene inspector — reads the current scene's collection hierarchy,
objects, materials, modifiers, shape keys, and physics setup.

Provides both a compact overview (for the system prompt) and detailed
per-object / per-collection inspection (for on-demand AI queries).
"""
from __future__ import annotations


# ---------------------------------------------------------------------------
# Compact overview  (injected into every system prompt)
# ---------------------------------------------------------------------------

def get_scene_overview() -> str:
    """Return a concise Chinese-language scene summary for the AI system prompt.

    Keeps output short to save tokens — just the collection tree,
    object counts by type, and active object info.
    """
    try:
        import bpy
    except ImportError:
        return "（Blender 未连接，无法读取场景）"

    scene = bpy.context.scene
    lines: list[str] = []

    # --- Collection tree (max 3 levels) ---
    lines.append("场景集合:")
    root = scene.collection
    _walk_collection(root, lines, indent=1, max_depth=3)

    # --- Object type counts ---
    type_counts: dict[str, int] = {}
    for obj in scene.objects:
        type_counts[obj.type] = type_counts.get(obj.type, 0) + 1
    if type_counts:
        parts = [f"{_type_zh(t)} {c}" for t, c in sorted(type_counts.items())]
        lines.append(f"对象统计: {', '.join(parts)}")

    # --- Active object ---
    active = bpy.context.view_layer.objects.active
    if active:
        lines.append(f"当前选中: {active.name} ({_type_zh(active.type)})")

    # --- Total faces / verts for meshes ---
    total_verts = 0
    total_faces = 0
    for obj in scene.objects:
        if obj.type == 'MESH':
            total_verts += len(obj.data.vertices)
            total_faces += len(obj.data.polygons)
    if total_verts > 0:
        lines.append(f"网格总计: {total_verts} 顶点, {total_faces} 面")

    return "\n".join(lines)


def _walk_collection(col, lines: list[str], indent: int, max_depth: int):
    """Recursively walk collection tree, appending indented lines."""
    if max_depth <= 0:
        return
    obj_count = len(col.objects)
    child_count = len(col.children)
    suffix_parts = []
    if obj_count:
        suffix_parts.append(f"{obj_count}个对象")
    if child_count:
        suffix_parts.append(f"{child_count}个子集合")
    suffix = f" ({', '.join(suffix_parts)})" if suffix_parts else ""
    prefix = "  " * indent
    lines.append(f"{prefix}📁 {col.name}{suffix}")

    # List objects directly in this collection (brief)
    for obj in col.objects:
        lines.append(f"{prefix}  · {obj.name} [{_type_zh(obj.type)}]")

    for child in col.children:
        _walk_collection(child, lines, indent + 1, max_depth - 1)


# ---------------------------------------------------------------------------
# Detailed collection inspection
# ---------------------------------------------------------------------------

def inspect_collection(collection_name: str) -> dict:
    """Return detailed info about a specific collection and its contents."""
    try:
        import bpy
    except ImportError:
        return {"success": False, "error": "Blender 未连接"}

    col = bpy.data.collections.get(collection_name)
    # Also check scene root collection
    if col is None and bpy.context.scene.collection.name == collection_name:
        col = bpy.context.scene.collection

    if col is None:
        available = [c.name for c in bpy.data.collections]
        available.insert(0, bpy.context.scene.collection.name)
        return {
            "success": False,
            "error": f"未找到集合 '{collection_name}'",
            "available_collections": available,
        }

    objects_info = []
    for obj in col.objects:
        objects_info.append(_summarize_object(obj))

    children = [c.name for c in col.children]

    return {
        "success": True,
        "collection": collection_name,
        "object_count": len(col.objects),
        "child_collections": children,
        "objects": objects_info,
    }


# ---------------------------------------------------------------------------
# Detailed object inspection
# ---------------------------------------------------------------------------

def inspect_object(object_name: str) -> dict:
    """Return detailed info about a specific Blender object."""
    try:
        import bpy
    except ImportError:
        return {"success": False, "error": "Blender 未连接"}

    obj = bpy.data.objects.get(object_name)
    if obj is None:
        return {
            "success": False,
            "error": f"未找到对象 '{object_name}'",
            "available_objects": [o.name for o in bpy.context.scene.objects][:30],
        }

    info = _summarize_object(obj, detailed=True)
    info["success"] = True
    return info


def _summarize_object(obj, detailed: bool = False) -> dict:
    """Build a summary dict for one Blender object."""
    info: dict = {
        "name": obj.name,
        "type": obj.type,
        "type_zh": _type_zh(obj.type),
        "location": [round(v, 4) for v in obj.location],
        "visible": obj.visible_get(),
    }

    # Custom properties (filter aimm_* ones)
    custom = {k: obj[k] for k in obj.keys() if not k.startswith("_")}
    if custom:
        # Convert to JSON-safe types
        safe_custom = {}
        for k, v in custom.items():
            try:
                if isinstance(v, (int, float, str, bool)):
                    safe_custom[k] = v
                else:
                    safe_custom[k] = str(v)
            except Exception:
                safe_custom[k] = "<不可序列化>"
        info["custom_properties"] = safe_custom

    # --- Type-specific data ---
    if obj.type == 'MESH':
        mesh = obj.data
        info["vertices"] = len(mesh.vertices)
        info["faces"] = len(mesh.polygons)
        info["edges"] = len(mesh.edges)

        # Materials
        mat_names = [slot.material.name if slot.material else "(空)" for slot in obj.material_slots]
        if mat_names:
            info["materials"] = mat_names

        # Shape keys
        if mesh.shape_keys:
            sk_names = [sk.name for sk in mesh.shape_keys.key_blocks]
            info["shape_keys"] = sk_names
            info["shape_key_count"] = len(sk_names)

        # Vertex groups
        if obj.vertex_groups:
            vg_names = [vg.name for vg in obj.vertex_groups]
            if detailed:
                info["vertex_groups"] = vg_names
            info["vertex_group_count"] = len(vg_names)

        if detailed:
            # UV maps
            uv_names = [uv.name for uv in mesh.uv_layers]
            if uv_names:
                info["uv_maps"] = uv_names

    elif obj.type == 'ARMATURE':
        arm = obj.data
        bone_names = [b.name for b in arm.bones]
        info["bone_count"] = len(bone_names)
        if detailed:
            info["bones"] = bone_names

    elif obj.type == 'EMPTY':
        info["empty_display_type"] = obj.empty_display_type

    elif obj.type in ('CAMERA', 'LIGHT'):
        if detailed and obj.type == 'LIGHT':
            info["light_type"] = obj.data.type
            info["energy"] = obj.data.energy

    # --- Modifiers ---
    if obj.modifiers:
        mod_list = [{"name": m.name, "type": m.type} for m in obj.modifiers]
        info["modifiers"] = mod_list

    # --- Physics ---
    if obj.rigid_body:
        info["rigid_body"] = {
            "type": obj.rigid_body.type,
            "mass": obj.rigid_body.mass,
            "enabled": obj.rigid_body.enabled,
        }
    if obj.rigid_body_constraint:
        info["rigid_body_constraint"] = {
            "type": obj.rigid_body_constraint.type,
            "enabled": obj.rigid_body_constraint.enabled,
        }

    # --- Parent ---
    if obj.parent:
        info["parent"] = obj.parent.name

    # --- Children ---
    children = [c.name for c in obj.children]
    if children:
        info["children"] = children

    return info


# ---------------------------------------------------------------------------
# Full scene snapshot (for inspect_scene command)
# ---------------------------------------------------------------------------

def get_scene_snapshot() -> dict:
    """Return a structured snapshot of the entire scene."""
    try:
        import bpy
    except ImportError:
        return {"success": False, "error": "Blender 未连接"}

    scene = bpy.context.scene

    # Collection tree
    collections = _snapshot_collection(scene.collection)

    # Object type breakdown
    type_counts: dict[str, int] = {}
    for obj in scene.objects:
        type_counts[obj.type] = type_counts.get(obj.type, 0) + 1

    # Materials in use
    materials_in_use = set()
    for obj in scene.objects:
        if obj.type == 'MESH':
            for slot in obj.material_slots:
                if slot.material:
                    materials_in_use.add(slot.material.name)

    # Active object
    active = bpy.context.view_layer.objects.active
    active_info = None
    if active:
        active_info = _summarize_object(active, detailed=True)

    return {
        "success": True,
        "scene_name": scene.name,
        "total_objects": len(scene.objects),
        "type_counts": {_type_zh(k): v for k, v in type_counts.items()},
        "collections": collections,
        "materials_in_use": sorted(materials_in_use),
        "active_object": active_info,
        "frame_current": scene.frame_current,
        "frame_range": [scene.frame_start, scene.frame_end],
    }


def _snapshot_collection(col) -> dict:
    """Recursively snapshot a collection."""
    return {
        "name": col.name,
        "objects": [obj.name for obj in col.objects],
        "children": [_snapshot_collection(c) for c in col.children],
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TYPE_ZH = {
    "MESH": "网格",
    "ARMATURE": "骨骼",
    "EMPTY": "空物体",
    "CAMERA": "相机",
    "LIGHT": "灯光",
    "CURVE": "曲线",
    "SURFACE": "曲面",
    "FONT": "文字",
    "GPENCIL": "蜡笔",
    "LATTICE": "晶格",
    "SPEAKER": "扬声器",
    "VOLUME": "体积",
}


def _type_zh(type_str: str) -> str:
    return _TYPE_ZH.get(type_str, type_str)
