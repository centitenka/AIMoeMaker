"""
Clothing mesh generation.
Creates parametric clothing meshes based on body dimensions.
"""
import bpy
import bmesh
import math
from mathutils import Vector
from .utils import (
    find_aimm_object, create_material, move_to_collection,
    set_active, hex_to_rgb
)


# Clothing type definitions: parameters for mesh generation
CLOTHING_TYPES = {
    "shirt": {"covers": "torso_upper", "offset": 0.008, "length_factor": 0.28},
    "t_shirt": {"covers": "torso_upper", "offset": 0.007, "length_factor": 0.25},
    "blouse": {"covers": "torso_upper", "offset": 0.01, "length_factor": 0.30},
    "jacket": {"covers": "torso_upper", "offset": 0.015, "length_factor": 0.35},
    "skirt": {"covers": "lower", "offset": 0.01, "length_factor": 0.25},
    "long_skirt": {"covers": "lower", "offset": 0.01, "length_factor": 0.45},
    "dress": {"covers": "full", "offset": 0.01, "length_factor": 0.55},
    "gothic_dress": {"covers": "full", "offset": 0.012, "length_factor": 0.60},
    "school_uniform": {"covers": "full", "offset": 0.008, "length_factor": 0.40},
    "shorts": {"covers": "lower", "offset": 0.008, "length_factor": 0.12},
    "pants": {"covers": "lower", "offset": 0.008, "length_factor": 0.42},
}


def create_clothing(clothing_type: str, color: str, height_cm: float, index: int = 0):
    """
    Generate a clothing mesh based on type and body dimensions.

    Uses a cylinder/cone approach offset from the body center line,
    then sculpts it to match the clothing silhouette.
    """
    config = CLOTHING_TYPES.get(clothing_type, CLOTHING_TYPES.get("dress"))
    if config is None:
        config = {"covers": "full", "offset": 0.01, "length_factor": 0.40}

    h = height_cm / 100.0
    offset = config["offset"]
    length = h * config["length_factor"]
    covers = config["covers"]

    # Determine vertical position based on what the clothing covers
    if covers == "torso_upper":
        top_z = h * 0.78  # Neck base
        bottom_z = h * 0.78 - length
        base_radius = h * 0.09 + offset
    elif covers == "lower":
        top_z = h * 0.55  # Waist
        bottom_z = h * 0.55 - length
        base_radius = h * 0.10 + offset
    else:  # "full"
        top_z = h * 0.78
        bottom_z = h * 0.78 - length
        base_radius = h * 0.09 + offset

    center_z = (top_z + bottom_z) / 2
    cloth_height = top_z - bottom_z

    # Create cylinder base
    segments = 24
    bpy.ops.mesh.primitive_cylinder_add(
        radius=base_radius,
        depth=cloth_height,
        vertices=segments,
        location=(0, 0, center_z),
    )
    cloth = bpy.context.active_object

    # Shape the clothing using bmesh vertex manipulation
    bm = bmesh.new()
    bm.from_mesh(cloth.data)
    bm.verts.ensure_lookup_table()

    for v in bm.verts:
        # Normalize Z position within clothing (0=bottom, 1=top)
        local_z = (v.co.z + cloth_height / 2) / cloth_height if cloth_height > 0 else 0.5

        if covers == "full" or covers == "torso_upper":
            # Taper at waist (middle area)
            waist_factor = 1.0 - 0.15 * math.sin(local_z * math.pi)
            v.co.x *= waist_factor
            v.co.y *= waist_factor * 0.85  # Flatter front-back

            # Bust area (upper portion)
            if local_z > 0.7:
                bust_factor = 1.0 + 0.1 * (local_z - 0.7) / 0.3
                v.co.y *= bust_factor

        if covers == "lower" or (covers == "full" and local_z < 0.35):
            # Flare at bottom for skirts/dresses
            if clothing_type in ("skirt", "long_skirt", "dress", "gothic_dress"):
                flare = 1.0 + (1.0 - local_z) * 0.4
                v.co.x *= flare
                v.co.y *= flare * 0.9

        # Slight Y offset for depth (clothing isn't perfectly centered)
        v.co.y *= 0.85

    bm.to_mesh(cloth.data)
    bm.free()

    # Material — assign immediately after mesh shaping to ensure valid material
    # before any operation (edit mode, shade_smooth, modifiers) that may trigger
    # depsgraph evaluation
    mat = create_material(f"AIMoeMaker_Cloth_{index}", color)
    cloth.data.materials.append(mat)

    # Delete top and bottom faces for open clothing look
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')

    # Select top/bottom caps
    bm = bmesh.from_edit_mesh(cloth.data)
    bm.faces.ensure_lookup_table()
    for face in bm.faces:
        center = face.calc_center_median()
        if abs(center.z - cloth_height / 2) < 0.001 or abs(center.z + cloth_height / 2) < 0.001:
            face.select = True
    bmesh.update_edit_mesh(cloth.data)
    bpy.ops.mesh.delete(type='FACE')
    bpy.ops.object.mode_set(mode='OBJECT')

    # Smooth shading
    bpy.ops.object.shade_smooth()

    # Add subdivision for smoothness
    mod = cloth.modifiers.new("Subdivision", 'SUBSURF')
    mod.levels = 1
    mod.render_levels = 2

    # Add solidify for thickness
    solidify = cloth.modifiers.new("Solidify", 'SOLIDIFY')
    solidify.thickness = offset * 0.5
    solidify.offset = -1  # Grow outward

    # Name and tag
    cloth.name = f"AIMoeMaker_Clothing_{index}"
    cloth["aimm_type"] = "clothing"
    cloth["aimm_clothing_type"] = clothing_type
    cloth["aimm_clothing_index"] = index

    # Parent to body
    body = find_aimm_object("body")
    if body:
        cloth.parent = body

    move_to_collection(cloth, "AIMoeMaker")
    set_active(cloth)

    return cloth


def update_clothing_color(index: int, color: str):
    """Update the color of an existing clothing mesh."""
    for obj in bpy.data.objects:
        if obj.get("aimm_type") == "clothing" and obj.get("aimm_clothing_index") == index:
            mat_name = f"AIMoeMaker_Cloth_{index}"
            mat = create_material(mat_name, color)
            if obj.data.materials:
                obj.data.materials[0] = mat
            else:
                obj.data.materials.append(mat)
            break
