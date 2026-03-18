# pipeline/mesh_validation.py
"""
Stage 1: Mesh validation and auto-repair before PMX export.
"""


def validate_and_repair(body_obj) -> dict:
    """
    Validate mesh geometry and attempt auto-repair.

    Checks:
    - Non-manifold edges
    - Duplicate vertices
    - Flipped normals
    - Zero-area faces

    Returns: {"success": bool, "warnings": list[str], "repairs": list[str]}
    """
    import bpy
    import bmesh

    if body_obj is None or body_obj.type != 'MESH':
        return {"success": False, "warnings": ["未找到网格对象"]}

    warnings = []
    repairs = []

    # Switch to edit mode for bmesh operations
    bpy.context.view_layer.objects.active = body_obj
    bpy.ops.object.mode_set(mode='EDIT')

    bm = bmesh.from_edit_mesh(body_obj.data)

    # Check for duplicate vertices
    before = len(bm.verts)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
    after = len(bm.verts)
    if before != after:
        repairs.append(f"移除了 {before - after} 个重叠顶点")

    # Check for non-manifold edges
    non_manifold = [e for e in bm.edges if not e.is_manifold and not e.is_boundary]
    if non_manifold:
        warnings.append(f"发现 {len(non_manifold)} 条非流形边")

    # Check for zero-area faces
    zero_faces = [f for f in bm.faces if f.calc_area() < 1e-8]
    if zero_faces:
        bmesh.ops.delete(bm, geom=zero_faces, context='FACES')
        repairs.append(f"移除了 {len(zero_faces)} 个零面积面")

    bmesh.update_edit_mesh(body_obj.data)
    bpy.ops.object.mode_set(mode='OBJECT')

    # Recalculate normals
    bpy.ops.object.select_all(action='DESELECT')
    body_obj.select_set(True)
    bpy.context.view_layer.objects.active = body_obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    repairs.append("已重新计算法线方向")

    # Apply all modifiers
    for mod in body_obj.modifiers:
        try:
            bpy.ops.object.modifier_apply(modifier=mod.name)
            repairs.append(f"已应用修改器: {mod.name}")
        except Exception:
            warnings.append(f"无法应用修改器: {mod.name}")

    return {
        "success": True,
        "warnings": warnings,
        "repairs": repairs,
    }
