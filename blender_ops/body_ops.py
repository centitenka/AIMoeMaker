"""
Parametric humanoid body generation using Blender's Skin modifier.
Creates a smooth organic anime-style body from a vertex skeleton.
"""
import bpy
import bmesh
from mathutils import Vector
from blender_ops.utils import remove_aimm_objects, create_material, move_to_collection, set_active


def create_body(height_cm: float, body_type: str, bust: float, waist: float, hip: float, head_ratio: float):
    """Create a parametric humanoid body mesh using Skin modifier."""
    remove_aimm_objects("body")
    remove_aimm_objects("eye")

    h = height_cm / 100.0  # meters
    head_count = 6.0 + (1.0 - head_ratio) * 2.5
    hs = h / head_count  # head size

    # --- Define body skeleton vertices and edges ---
    # Positions as (x, y, z) in meters, (rx, ry) = skin radius x, y
    # We build one half and mirror, or define full symmetry

    # Torso centerline
    crotch_z = h * 0.45
    waist_z = h * 0.55
    chest_z = h * 0.68
    shoulder_z = h * 0.77
    neck_base_z = h * 0.80
    neck_top_z = h * 0.84
    head_center_z = h * 0.92
    head_top_z = h * 1.0

    shoulder_w = h * 0.17
    hip_w = h * 0.09 * (0.8 + hip * 0.4)

    waist_rx = h * 0.06 * (0.6 + (1 - waist) * 0.4)
    waist_ry = h * 0.04
    chest_rx = h * 0.07 * (0.7 + bust * 0.5)
    chest_ry = h * 0.055 * (0.8 + bust * 0.4)
    hip_rx = h * 0.08 * (0.8 + hip * 0.3)
    hip_ry = h * 0.055

    leg_r = h * 0.04
    arm_r = h * 0.022

    knee_z = h * 0.25
    ankle_z = h * 0.04
    toe_z = 0.0

    elbow_z = h * 0.55
    wrist_z = h * 0.42
    hand_z = h * 0.38

    # Vertex list: (x, y, z, skin_rx, skin_ry)
    verts = [
        # 0: head top
        (0, 0, head_top_z, hs * 0.01, hs * 0.01),
        # 1: head center
        (0, 0, head_center_z, hs * 0.42, hs * 0.38),
        # 2: neck top
        (0, 0, neck_top_z, h * 0.025, h * 0.022),
        # 3: neck base
        (0, 0, neck_base_z, h * 0.03, h * 0.025),
        # 4: shoulder center
        (0, 0, shoulder_z, h * 0.05, h * 0.04),
        # 5: chest
        (0, 0, chest_z, chest_rx, chest_ry),
        # 6: waist
        (0, 0, waist_z, waist_rx, waist_ry),
        # 7: hip center / crotch
        (0, 0, crotch_z, h * 0.04, h * 0.03),

        # Left arm: 8-11
        # 8: left shoulder
        (shoulder_w, 0, shoulder_z, arm_r * 1.3, arm_r * 1.3),
        # 9: left elbow
        (shoulder_w + h * 0.02, 0, elbow_z, arm_r, arm_r),
        # 10: left wrist
        (shoulder_w + h * 0.03, 0, wrist_z, arm_r * 0.8, arm_r * 0.5),
        # 11: left hand
        (shoulder_w + h * 0.03, 0, hand_z, arm_r * 1.0, arm_r * 0.3),

        # Right arm: 12-15
        # 12: right shoulder
        (-shoulder_w, 0, shoulder_z, arm_r * 1.3, arm_r * 1.3),
        # 13: right elbow
        (-shoulder_w - h * 0.02, 0, elbow_z, arm_r, arm_r),
        # 14: right wrist
        (-shoulder_w - h * 0.03, 0, wrist_z, arm_r * 0.8, arm_r * 0.5),
        # 15: right hand
        (-shoulder_w - h * 0.03, 0, hand_z, arm_r * 1.0, arm_r * 0.3),

        # Left leg: 16-19
        # 16: left hip
        (hip_w, 0, crotch_z, hip_rx, hip_ry),
        # 17: left knee
        (hip_w, 0, knee_z, leg_r * 0.9, leg_r * 0.9),
        # 18: left ankle
        (hip_w, 0, ankle_z, leg_r * 0.7, leg_r * 0.5),
        # 19: left toe
        (hip_w, h * 0.04, toe_z, leg_r * 0.6, leg_r * 0.2),

        # Right leg: 20-23
        # 20: right hip
        (-hip_w, 0, crotch_z, hip_rx, hip_ry),
        # 21: right knee
        (-hip_w, 0, knee_z, leg_r * 0.9, leg_r * 0.9),
        # 22: right ankle
        (-hip_w, 0, ankle_z, leg_r * 0.7, leg_r * 0.5),
        # 23: right toe
        (-hip_w, h * 0.04, toe_z, leg_r * 0.6, leg_r * 0.2),
    ]

    # Edges (vertex index pairs)
    edges = [
        # Spine
        (0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7),
        # Left arm
        (4, 8), (8, 9), (9, 10), (10, 11),
        # Right arm
        (4, 12), (12, 13), (13, 14), (14, 15),
        # Left leg
        (7, 16), (16, 17), (17, 18), (18, 19),
        # Right leg
        (7, 20), (20, 21), (21, 22), (22, 23),
    ]

    # --- Create mesh from vertices and edges ---
    mesh = bpy.data.meshes.new("AIMoeMaker_Body_Mesh")
    positions = [(v[0], v[1], v[2]) for v in verts]
    mesh.from_pydata(positions, edges, [])
    mesh.update()

    body = bpy.data.objects.new("AIMoeMaker_Body", mesh)
    bpy.context.collection.objects.link(body)
    set_active(body)

    # --- Apply Skin modifier ---
    skin_mod = body.modifiers.new("Skin", 'SKIN')

    # Set skin radii per vertex
    for i, v_data in enumerate(verts):
        sv = mesh.skin_vertices[""].data[i]
        sv.radius = (v_data[3], v_data[4])
        # Mark root vertex
        if i == 4:  # shoulder center as root
            sv.use_root = True

    # --- Apply Subdivision for smoothness ---
    sub_mod = body.modifiers.new("Subdivision", 'SUBSURF')
    sub_mod.levels = 2
    sub_mod.render_levels = 3

    # --- Apply modifiers to get final mesh ---
    bpy.ops.object.modifier_apply(modifier="Skin")
    bpy.ops.object.modifier_apply(modifier="Subdivision")

    # Smooth shading
    bpy.ops.object.shade_smooth()

    # Recalculate normals
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')

    # Custom properties
    body["aimm_type"] = "body"
    body["aimm_height"] = height_cm
    body["aimm_body_type"] = body_type

    # Apply skin material
    mat = create_material("AIMoeMaker_Skin", "#FFE0BD")
    body.data.materials.append(mat)

    move_to_collection(body, "AIMoeMaker")
    set_active(body)

    return body


def apply_height(height_cm: float):
    """Scale existing body to new height."""
    from blender_ops.utils import find_aimm_object
    body = find_aimm_object("body")
    if body is None:
        return

    old_height = body.get("aimm_height", 158.0)
    if old_height <= 0:
        return
    scale = height_cm / old_height
    body.scale *= scale
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    body["aimm_height"] = height_cm
