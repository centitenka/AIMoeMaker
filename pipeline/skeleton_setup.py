# pipeline/skeleton_setup.py
"""
Stage 2: Verify and fix skeleton for MMD PMX compatibility.
"""

# Required MMD bones for a valid PMX model
REQUIRED_BONES = [
    "全ての親", "センター", "上半身", "首", "頭",
    "左肩", "左腕", "左ひじ", "左手首",
    "右肩", "右腕", "右ひじ", "右手首",
    "下半身",
    "左足", "左ひざ", "左足首",
    "右足", "右ひざ", "右足首",
    "左足ＩＫ", "右足ＩＫ",
]


def verify_skeleton(armature_obj) -> dict:
    """
    Verify the armature has all required MMD bones.

    Returns: {"success": bool, "missing_bones": list[str], "extra_bones": list[str]}
    """
    import bpy

    if armature_obj is None or armature_obj.type != 'ARMATURE':
        return {"success": False, "missing_bones": REQUIRED_BONES, "extra_bones": []}

    existing = set(bone.name for bone in armature_obj.data.bones)
    required = set(REQUIRED_BONES)

    missing = required - existing
    extra = existing - required

    return {
        "success": len(missing) == 0,
        "missing_bones": sorted(missing),
        "extra_bones": sorted(extra),
        "bone_count": len(existing),
    }


def rename_bones_for_pmx(armature_obj) -> dict:
    """
    Ensure bones have both Japanese and English names.
    MMD tools expects specific naming conventions.
    """
    import bpy

    if armature_obj is None or armature_obj.type != 'ARMATURE':
        return {"success": False, "error": "无骨骼对象"}

    # Bone name mapping (JP -> EN) from our skeleton_ops
    from ..blender_ops.skeleton_ops import MMD_BONES
    jp_to_en = {bone[0]: bone[1] for bone in MMD_BONES}

    renamed = 0
    for bone in armature_obj.data.bones:
        # mmd_tools stores English name in a custom property or bone's name_en
        if bone.name in jp_to_en:
            # Set the bone's name as Japanese, store English as property
            if "mmd_bone_name_e" not in bone:
                bone["mmd_bone_name_e"] = jp_to_en[bone.name]
                renamed += 1

    return {"success": True, "renamed": renamed}
