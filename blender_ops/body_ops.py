"""
Parametric body mesh generation using Blender primitives.
Creates a recognizable anime-style humanoid silhouette.
"""
import bpy
import bmesh
from mathutils import Vector
from blender_ops.utils import remove_aimm_objects, create_material, move_to_collection, set_active


def create_body(height_cm: float, body_type: str, bust: float, waist: float, hip: float, head_ratio: float):
    """
    Create a parametric humanoid body mesh.

    Args:
        height_cm: Total height in centimeters
        body_type: "loli", "teen", "default", "adult"
        bust/waist/hip: 0-1 proportion values
        head_ratio: 0-1 head size ratio
    """
    # Remove existing body
    remove_aimm_objects("body")

    height = height_cm / 100.0  # Convert to meters (Blender units)

    # Head size determines body proportions
    # Anime characters typically 6-8 heads tall
    head_count = 6.0 + (1.0 - head_ratio) * 2.5  # head_ratio 0->8.5 heads, 1->6 heads
    head_size = height / head_count

    # Create body parts collection
    parts = []

    # --- Head ---
    head_radius = head_size * 0.45
    head_z = height - head_size * 0.5
    bpy.ops.mesh.primitive_uv_sphere_add(radius=head_radius, segments=16, ring_count=12, location=(0, 0, head_z))
    head = bpy.context.active_object
    head.scale.y = 0.85  # Slightly flatten front-back
    bpy.ops.object.transform_apply(scale=True)
    parts.append(head)

    # --- Neck ---
    neck_radius = head_radius * 0.35
    neck_height = head_size * 0.3
    neck_z = height - head_size - neck_height * 0.5
    bpy.ops.mesh.primitive_cylinder_add(radius=neck_radius, depth=neck_height, location=(0, 0, neck_z), vertices=12)
    parts.append(bpy.context.active_object)

    # --- Torso (upper body) ---
    torso_top = neck_z - neck_height * 0.5
    torso_height = height * 0.25
    torso_z = torso_top - torso_height * 0.5

    shoulder_width = height * 0.18
    bust_depth = 0.08 + bust * 0.06  # bust affects front depth
    waist_scale = 0.6 + (1 - waist) * 0.25  # waist affects narrowing

    bpy.ops.mesh.primitive_cylinder_add(radius=shoulder_width, depth=torso_height, location=(0, 0, torso_z), vertices=16)
    torso = bpy.context.active_object
    torso.scale.y = bust_depth / shoulder_width if shoulder_width > 0 else 0.6

    # Taper the waist using a simple lattice-like edit
    bm = bmesh.new()
    bm.from_mesh(torso.data)
    for v in bm.verts:
        # Lower vertices get narrower (waist)
        local_z = (v.co.z + torso_height/2) / torso_height  # 0=bottom, 1=top
        taper = 1.0 - (1.0 - waist_scale) * (1.0 - local_z)
        v.co.x *= taper
        v.co.y *= taper
    bm.to_mesh(torso.data)
    bm.free()
    bpy.ops.object.transform_apply(scale=True)
    parts.append(torso)

    # --- Lower body (hips) ---
    hip_top = torso_z - torso_height * 0.5
    hip_height = height * 0.12
    hip_z = hip_top - hip_height * 0.5
    hip_width = shoulder_width * (0.8 + hip * 0.4)

    bpy.ops.mesh.primitive_cylinder_add(radius=hip_width, depth=hip_height, location=(0, 0, hip_z), vertices=16)
    hip_obj = bpy.context.active_object
    hip_obj.scale.y = 0.7
    bpy.ops.object.transform_apply(scale=True)
    parts.append(hip_obj)

    # --- Legs ---
    leg_top = hip_z - hip_height * 0.5
    leg_length = leg_top  # Legs go from hip to ground
    leg_radius = height * 0.045
    leg_spacing = hip_width * 0.5

    for side in [-1, 1]:
        x = side * leg_spacing

        # Upper leg
        upper_len = leg_length * 0.5
        upper_z = leg_top - upper_len * 0.5
        bpy.ops.mesh.primitive_cylinder_add(radius=leg_radius * 1.2, depth=upper_len, location=(x, 0, upper_z), vertices=12)
        parts.append(bpy.context.active_object)

        # Lower leg
        lower_len = leg_length * 0.45
        lower_z = leg_top - upper_len - lower_len * 0.5
        bpy.ops.mesh.primitive_cylinder_add(radius=leg_radius, depth=lower_len, location=(x, 0, lower_z), vertices=12)
        parts.append(bpy.context.active_object)

        # Foot
        foot_z = lower_z - lower_len * 0.5
        bpy.ops.mesh.primitive_cube_add(size=0.02, location=(x, 0.02, foot_z))
        foot = bpy.context.active_object
        foot.scale = (leg_radius * 1.5, leg_radius * 3, leg_radius * 0.5)
        bpy.ops.object.transform_apply(scale=True)
        parts.append(foot)

    # --- Arms ---
    arm_top = torso_top - head_size * 0.1
    arm_length = height * 0.35
    arm_radius = height * 0.025

    for side in [-1, 1]:
        x = side * (shoulder_width + arm_radius)

        # Upper arm
        upper_len = arm_length * 0.5
        upper_z = arm_top - upper_len * 0.5
        bpy.ops.mesh.primitive_cylinder_add(radius=arm_radius * 1.1, depth=upper_len, location=(x, 0, upper_z), vertices=10)
        parts.append(bpy.context.active_object)

        # Lower arm
        lower_len = arm_length * 0.45
        lower_z = arm_top - upper_len - lower_len * 0.5
        bpy.ops.mesh.primitive_cylinder_add(radius=arm_radius * 0.9, depth=lower_len, location=(x, 0, lower_z), vertices=10)
        parts.append(bpy.context.active_object)

        # Hand
        hand_z = lower_z - lower_len * 0.5 - arm_radius
        bpy.ops.mesh.primitive_uv_sphere_add(radius=arm_radius * 1.5, location=(x, 0, hand_z), segments=8, ring_count=6)
        hand = bpy.context.active_object
        hand.scale.z = 0.6
        bpy.ops.object.transform_apply(scale=True)
        parts.append(hand)

    # --- Join all parts ---
    bpy.ops.object.select_all(action='DESELECT')
    for part in parts:
        part.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()

    body = bpy.context.active_object
    body.name = "AIMoeMaker_Body"
    body["aimm_type"] = "body"
    body["aimm_height"] = height_cm
    body["aimm_body_type"] = body_type

    # Apply skin material
    mat = create_material("AIMoeMaker_Skin", "#FFE0BD")
    if body.data.materials:
        body.data.materials[0] = mat
    else:
        body.data.materials.append(mat)

    # Smooth shading
    bpy.ops.object.shade_smooth()

    # Add subdivision modifier for smoother look
    mod = body.modifiers.new("Subdivision", 'SUBSURF')
    mod.levels = 1
    mod.render_levels = 2

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
    scale = height_cm / old_height
    body.scale *= scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    body["aimm_height"] = height_cm
