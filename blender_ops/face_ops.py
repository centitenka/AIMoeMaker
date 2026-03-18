"""
Face detail mesh generation: anime-style eyes, nose, mouth indicators.
"""
import bpy
import math
from mathutils import Vector
from blender_ops.utils import (
    remove_aimm_objects, find_aimm_object, create_material,
    move_to_collection, set_active, hex_to_rgb
)


# Eye shape parameters: (scale_x, scale_y, scale_z) relative to base
EYE_SHAPE_PARAMS = {
    "round":   (1.0, 0.5, 1.0),
    "almond":  (1.2, 0.4, 0.85),
    "cat":     (1.15, 0.4, 0.9),
    "droopy":  (1.1, 0.5, 0.95),
    "tsurime": (1.1, 0.4, 0.85),
    "tareme":  (1.05, 0.5, 1.05),
}


def create_eyes(eye_shape: str, eye_color: str, head_height_z: float, head_radius: float):
    """
    Create anime-style eye meshes.

    Each eye consists of 3 layers:
    - Sclera (white outer shell)
    - Iris (colored disc)
    - Pupil (black inner disc)
    """
    remove_aimm_objects("eye")

    shape_params = EYE_SHAPE_PARAMS.get(eye_shape, EYE_SHAPE_PARAMS["round"])

    eye_z = head_height_z - head_radius * 0.15  # Slightly below center
    eye_spacing = head_radius * 0.45
    eye_base_size = head_radius * 0.22

    eyes = []

    for side in [-1, 1]:
        x = side * eye_spacing
        y = -head_radius * 0.85  # In front of head

        # Sclera (white part)
        bpy.ops.mesh.primitive_uv_sphere_add(
            segments=16, ring_count=12,
            radius=eye_base_size,
            location=(x, y, eye_z)
        )
        sclera = bpy.context.active_object
        sclera.scale = (shape_params[0], shape_params[1], shape_params[2])
        bpy.ops.object.transform_apply(scale=True)
        sclera.name = f"AIMoeMaker_Eye_{'L' if side > 0 else 'R'}"
        sclera["aimm_type"] = "eye"

        # White material
        sclera_mat = create_material("AIMoeMaker_Sclera", "#FFFFFF")
        sclera.data.materials.append(sclera_mat)
        bpy.ops.object.shade_smooth()
        eyes.append(sclera)

        # Iris (colored disc)
        iris_size = eye_base_size * 0.65
        bpy.ops.mesh.primitive_uv_sphere_add(
            segments=16, ring_count=12,
            radius=iris_size,
            location=(x, y - eye_base_size * shape_params[1] * 0.5, eye_z)
        )
        iris = bpy.context.active_object
        iris.scale = (0.8 * shape_params[0], 0.3, 0.85 * shape_params[2])
        bpy.ops.object.transform_apply(scale=True)
        iris.name = f"AIMoeMaker_Iris_{'L' if side > 0 else 'R'}"
        iris["aimm_type"] = "eye"

        # Iris material with the eye color
        iris_mat = _create_eye_material(f"AIMoeMaker_Iris_{'L' if side > 0 else 'R'}", eye_color)
        iris.data.materials.append(iris_mat)
        bpy.ops.object.shade_smooth()
        eyes.append(iris)

        # Pupil (small dark center)
        pupil_size = iris_size * 0.4
        bpy.ops.mesh.primitive_uv_sphere_add(
            segments=12, ring_count=8,
            radius=pupil_size,
            location=(x, y - eye_base_size * shape_params[1] * 0.7, eye_z)
        )
        pupil = bpy.context.active_object
        pupil.scale = (0.6, 0.2, 0.6)
        bpy.ops.object.transform_apply(scale=True)
        pupil.name = f"AIMoeMaker_Pupil_{'L' if side > 0 else 'R'}"
        pupil["aimm_type"] = "eye"

        pupil_mat = create_material("AIMoeMaker_Pupil", "#111111")
        pupil.data.materials.append(pupil_mat)
        bpy.ops.object.shade_smooth()
        eyes.append(pupil)

    # Move all eye parts to collection
    for eye_obj in eyes:
        move_to_collection(eye_obj, "AIMoeMaker")

    # Parent eyes to body if it exists
    body = find_aimm_object("body")
    if body:
        for eye_obj in eyes:
            eye_obj.parent = body

    return eyes


def update_eye_color(eye_color: str):
    """Update the iris color on existing eye meshes."""
    import bpy
    for obj in bpy.data.objects:
        if obj.get("aimm_type") == "eye" and "Iris" in obj.name:
            if obj.data.materials:
                _update_eye_material(obj.data.materials[0], eye_color)
            else:
                mat = _create_eye_material(obj.name + "_mat", eye_color)
                obj.data.materials.append(mat)


def _create_eye_material(name: str, color_hex: str):
    """Create an anime-style eye material with slight emission for vibrancy."""
    import bpy
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    bsdf = nodes.get("Principled BSDF")
    if bsdf:
        r, g, b = hex_to_rgb(color_hex)
        bsdf.inputs["Base Color"].default_value = (r, g, b, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.1  # Glossy eyes
        bsdf.inputs["Specular IOR Level"].default_value = 0.8
        # Slight emission for anime vibrancy
        bsdf.inputs["Emission Color"].default_value = (r * 0.3, g * 0.3, b * 0.3, 1.0)
        bsdf.inputs["Emission Strength"].default_value = 0.2

    return mat


def _update_eye_material(mat, color_hex: str):
    """Update an existing eye material's color."""
    if mat and mat.use_nodes:
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            r, g, b = hex_to_rgb(color_hex)
            bsdf.inputs["Base Color"].default_value = (r, g, b, 1.0)
            bsdf.inputs["Emission Color"].default_value = (r * 0.3, g * 0.3, b * 0.3, 1.0)
