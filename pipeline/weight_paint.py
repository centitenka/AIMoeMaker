# pipeline/weight_paint.py
"""
Stage 3: Verify weight painting coverage.
"""


def verify_weights(body_obj, armature_obj) -> dict:
    """
    Check that all vertices have weight assignments.

    Returns: {"success": bool, "unweighted_count": int, "total_vertices": int}
    """
    import bpy

    if body_obj is None or body_obj.type != 'MESH':
        return {"success": False, "unweighted_count": 0, "total_vertices": 0}

    total = len(body_obj.data.vertices)
    unweighted = 0

    for vert in body_obj.data.vertices:
        if len(vert.groups) == 0:
            unweighted += 1

    return {
        "success": unweighted == 0,
        "unweighted_count": unweighted,
        "total_vertices": total,
        "coverage": f"{((total - unweighted) / total * 100) if total > 0 else 0:.1f}%",
    }


def fix_unweighted_vertices(body_obj, armature_obj) -> dict:
    """
    Assign unweighted vertices to the nearest bone's vertex group.
    """
    import bpy
    from mathutils import Vector

    if body_obj is None or armature_obj is None:
        return {"success": False, "error": "缺少对象"}

    if body_obj.type != 'MESH' or armature_obj.type != 'ARMATURE':
        return {"success": False, "error": "对象类型不正确"}

    fixed = 0

    # Get bone positions for nearest-bone assignment
    bone_positions = {}
    for bone in armature_obj.data.bones:
        bone_positions[bone.name] = (Vector(bone.head_local) + Vector(bone.tail_local)) * 0.5

    for vert in body_obj.data.vertices:
        if len(vert.groups) == 0:
            # Find nearest bone
            vert_pos = body_obj.matrix_world @ vert.co
            nearest_bone = None
            nearest_dist = float('inf')

            for bone_name, bone_pos in bone_positions.items():
                dist = (vert_pos - armature_obj.matrix_world @ bone_pos).length
                if dist < nearest_dist:
                    nearest_dist = dist
                    nearest_bone = bone_name

            if nearest_bone:
                # Ensure vertex group exists
                if nearest_bone not in body_obj.vertex_groups:
                    body_obj.vertex_groups.new(name=nearest_bone)

                vg = body_obj.vertex_groups[nearest_bone]
                vg.add([vert.index], 1.0, 'REPLACE')
                fixed += 1

    return {"success": True, "fixed": fixed}
