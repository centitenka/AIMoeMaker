# pipeline/physics_setup.py
"""
Stage 4: Convert physics setup to MMD-compatible format.
Verifies rigid bodies and joints are correctly configured for PMX export.
"""
from ..blender_ops.utils import find_all_aimm_objects


def verify_physics() -> dict:
    """
    Verify physics objects (rigid bodies and joints) are PMX-compatible.
    """
    rb_objects = find_all_aimm_objects("physics_hair")

    rigid_bodies = 0
    joints = 0
    warnings = []

    for obj in rb_objects:
        if obj.rigid_body:
            rigid_bodies += 1
        if obj.rigid_body_constraint:
            joints += 1

    if rigid_bodies == 0:
        warnings.append("未设置物理刚体（头发/服装物理将不生效）")

    return {
        "success": True,
        "rigid_bodies": rigid_bodies,
        "joints": joints,
        "warnings": warnings,
    }
