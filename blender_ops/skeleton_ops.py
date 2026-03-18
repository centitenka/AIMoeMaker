"""
MMD standard armature creation with correct bone hierarchy and positions.
"""
import bpy
from mathutils import Vector
from blender_ops.utils import remove_aimm_objects, find_aimm_object, move_to_collection, set_active

# MMD standard bone definitions: (name_jp, name_en, head_offset, tail_offset, parent_jp)
# Positions are relative to character standing at origin, facing -Y, height normalized to 1.0
MMD_BONES = [
    # Root
    ("全ての親", "root", (0, 0, 0), (0, 0, 0.05), None),
    ("センター", "center", (0, 0, 0.45), (0, 0, 0.35), "全ての親"),
    ("グルーブ", "groove", (0, 0, 0.45), (0, 0, 0.44), "センター"),

    # Upper body
    ("腰", "waist", (0, 0, 0.55), (0, 0, 0.57), "グルーブ"),
    ("上半身", "upper body", (0, 0, 0.57), (0, 0, 0.68), "腰"),
    ("上半身2", "upper body2", (0, 0, 0.68), (0, 0, 0.78), "上半身"),
    ("首", "neck", (0, 0, 0.78), (0, 0, 0.84), "上半身2"),
    ("頭", "head", (0, 0, 0.84), (0, 0, 1.0), "首"),

    # Left arm
    ("左肩", "shoulder_L", (0.02, 0, 0.77), (0.08, 0, 0.77), "上半身2"),
    ("左腕", "arm_L", (0.08, 0, 0.77), (0.20, 0, 0.68), "左肩"),
    ("左ひじ", "elbow_L", (0.20, 0, 0.68), (0.20, 0, 0.52), "左腕"),
    ("左手首", "wrist_L", (0.20, 0, 0.52), (0.20, 0, 0.47), "左ひじ"),

    # Right arm
    ("右肩", "shoulder_R", (-0.02, 0, 0.77), (-0.08, 0, 0.77), "上半身2"),
    ("右腕", "arm_R", (-0.08, 0, 0.77), (-0.20, 0, 0.68), "右肩"),
    ("右ひじ", "elbow_R", (-0.20, 0, 0.68), (-0.20, 0, 0.52), "右腕"),
    ("右手首", "wrist_R", (-0.20, 0, 0.52), (-0.20, 0, 0.47), "右ひじ"),

    # Lower body
    ("下半身", "lower body", (0, 0, 0.55), (0, 0, 0.50), "グルーブ"),

    # Left leg
    ("左足", "leg_L", (0.05, 0, 0.50), (0.05, 0, 0.28), "下半身"),
    ("左ひざ", "knee_L", (0.05, 0, 0.28), (0.05, 0, 0.05), "左足"),
    ("左足首", "ankle_L", (0.05, 0, 0.05), (0.05, 0.03, 0.0), "左ひざ"),
    ("左つま先", "toe_L", (0.05, 0.03, 0.0), (0.05, 0.08, 0.0), "左足首"),

    # Right leg
    ("右足", "leg_R", (-0.05, 0, 0.50), (-0.05, 0, 0.28), "下半身"),
    ("右ひざ", "knee_R", (-0.05, 0, 0.28), (-0.05, 0, 0.05), "右足"),
    ("右足首", "ankle_R", (-0.05, 0, 0.05), (-0.05, 0.03, 0.0), "右ひざ"),
    ("右つま先", "toe_R", (-0.05, 0.03, 0.0), (-0.05, 0.08, 0.0), "右足首"),

    # IK bones
    ("左足ＩＫ", "leg IK_L", (0.05, 0, 0.05), (0.05, 0.03, 0.0), None),
    ("右足ＩＫ", "leg IK_R", (-0.05, 0, 0.05), (-0.05, 0.03, 0.0), None),
    ("左つま先ＩＫ", "toe IK_L", (0.05, 0.03, 0.0), (0.05, 0.08, 0.0), "左足ＩＫ"),
    ("右つま先ＩＫ", "toe IK_R", (-0.05, 0.03, 0.0), (-0.05, 0.08, 0.0), "右足ＩＫ"),
]


def create_skeleton(height_cm: float):
    """
    Create MMD standard armature scaled to character height.

    Args:
        height_cm: Character height in centimeters
    """
    remove_aimm_objects("skeleton")

    height = height_cm / 100.0  # Convert to meters

    # Create armature
    arm_data = bpy.data.armatures.new("AIMoeMaker_Armature")
    arm_data.display_type = 'STICK'
    arm_obj = bpy.data.objects.new("AIMoeMaker_Skeleton", arm_data)
    bpy.context.collection.objects.link(arm_obj)
    arm_obj["aimm_type"] = "skeleton"

    set_active(arm_obj)
    bpy.ops.object.mode_set(mode='EDIT')

    bone_map = {}  # name_jp -> EditBone

    for name_jp, name_en, head_pos, tail_pos, parent_jp in MMD_BONES:
        bone = arm_data.edit_bones.new(name_jp)
        bone.head = Vector(head_pos) * height
        bone.tail = Vector(tail_pos) * height

        # Ensure bone has minimum length
        if (bone.tail - bone.head).length < 0.001:
            bone.tail = bone.head + Vector((0, 0, 0.01 * height))

        if parent_jp and parent_jp in bone_map:
            bone.parent = bone_map[parent_jp]

        bone_map[name_jp] = bone

    bpy.ops.object.mode_set(mode='OBJECT')

    # Setup IK constraints
    bpy.ops.object.mode_set(mode='POSE')
    pose = arm_obj.pose

    # Left leg IK
    if "左ひざ" in pose.bones and "左足ＩＫ" in arm_data.bones:
        ik = pose.bones["左ひざ"].constraints.new('IK')
        ik.target = arm_obj
        ik.subtarget = "左足ＩＫ"
        ik.chain_count = 2

    # Right leg IK
    if "右ひざ" in pose.bones and "右足ＩＫ" in arm_data.bones:
        ik = pose.bones["右ひざ"].constraints.new('IK')
        ik.target = arm_obj
        ik.subtarget = "右足ＩＫ"
        ik.chain_count = 2

    bpy.ops.object.mode_set(mode='OBJECT')

    move_to_collection(arm_obj, "AIMoeMaker")
    set_active(arm_obj)

    # Parent body mesh to armature if it exists
    body = find_aimm_object("body")
    if body:
        body.select_set(True)
        arm_obj.select_set(True)
        bpy.context.view_layer.objects.active = arm_obj
        bpy.ops.object.parent_set(type='ARMATURE_AUTO')

    return arm_obj


def auto_weight_paint(height_cm: float):
    """Apply automatic weight painting to body mesh."""
    body = find_aimm_object("body")
    skeleton = find_aimm_object("skeleton")

    if not body or not skeleton:
        return False

    # Re-parent with automatic weights
    bpy.ops.object.select_all(action='DESELECT')
    body.select_set(True)
    skeleton.select_set(True)
    bpy.context.view_layer.objects.active = skeleton
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')

    return True
