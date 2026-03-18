"""
Procedural hair generation using Blender curves.
"""
import bpy
import math
from mathutils import Vector
from blender_ops.utils import remove_aimm_objects, find_aimm_object, create_material, move_to_collection, set_active


# Hair style definitions: each style defines curve control points relative to head
HAIR_CONFIGS = {
    "short": {"strand_count": 12, "length_mult": 0.3, "spread": 0.8, "droop": 0.2},
    "long": {"strand_count": 16, "length_mult": 1.0, "spread": 0.9, "droop": 0.6},
    "twintail": {"strand_count": 20, "length_mult": 0.8, "spread": 1.0, "droop": 0.4, "bunches": 2},
    "ponytail": {"strand_count": 14, "length_mult": 0.7, "spread": 0.7, "droop": 0.5, "bunches": 1},
    "bob": {"strand_count": 14, "length_mult": 0.35, "spread": 1.0, "droop": 0.3},
    "hime_cut": {"strand_count": 18, "length_mult": 0.9, "spread": 0.95, "droop": 0.5},
    "braid": {"strand_count": 12, "length_mult": 0.6, "spread": 0.6, "droop": 0.7, "bunches": 1},
}


def create_hair(style: str, colors: list[str], length: float, gradient: bool, head_height: float):
    """
    Create procedural hair mesh.

    Args:
        style: Hair style name
        colors: List of hex color strings
        length: 0-1 length multiplier
        gradient: Whether to apply color gradient
        head_height: Z position of head center (meters)
    """
    remove_aimm_objects("hair")

    config = HAIR_CONFIGS.get(style, HAIR_CONFIGS["short"])
    strand_count = config["strand_count"]
    length_mult = config["length_mult"] * (0.5 + length * 0.5)
    spread = config["spread"]
    droop = config["droop"]

    head_radius = 0.12  # Approximate head radius
    hair_length = head_radius * 3 * length_mult

    curves = []

    # Generate hair strands around the head
    bunches = config.get("bunches", 0)

    for i in range(strand_count):
        angle = (i / strand_count) * math.pi * 2

        # Starting point on head surface
        start_x = math.cos(angle) * head_radius * spread
        start_y = math.sin(angle) * head_radius * spread * 0.8
        start_z = head_height + head_radius * 0.3

        # End point (hair falls down with some spread)
        droop_factor = droop + (1 - droop) * 0.3
        end_x = start_x * (1 + spread * 0.5)
        end_y = start_y * (1 + spread * 0.3)
        end_z = start_z - hair_length * droop_factor

        # Middle control point
        mid_x = (start_x + end_x) * 0.5
        mid_y = (start_y + end_y) * 0.5
        mid_z = (start_z + end_z) * 0.5 + hair_length * 0.1

        # Create curve
        curve_data = bpy.data.curves.new(f"hair_strand_{i}", 'CURVE')
        curve_data.dimensions = '3D'
        curve_data.bevel_depth = 0.008  # Strand thickness
        curve_data.bevel_resolution = 2

        spline = curve_data.splines.new('BEZIER')
        spline.bezier_points.add(2)  # 3 points total

        # Start
        p0 = spline.bezier_points[0]
        p0.co = Vector((start_x, start_y, start_z))
        p0.handle_right = p0.co + Vector((0, 0, -hair_length * 0.2))
        p0.handle_left = p0.co + Vector((0, 0, hair_length * 0.1))

        # Middle
        p1 = spline.bezier_points[1]
        p1.co = Vector((mid_x, mid_y, mid_z))
        p1.handle_left = p1.co + Vector((-0.02, 0, 0.02))
        p1.handle_right = p1.co + Vector((0.02, 0, -0.02))

        # End
        p2 = spline.bezier_points[2]
        p2.co = Vector((end_x, end_y, end_z))
        p2.handle_left = p2.co + Vector((0, 0, hair_length * 0.15))
        p2.handle_right = p2.co + Vector((0, 0, -0.02))

        curve_obj = bpy.data.objects.new(f"hair_strand_{i}", curve_data)
        bpy.context.collection.objects.link(curve_obj)
        curves.append(curve_obj)

    # Handle bunches (twintail, ponytail)
    if bunches == 2:
        _add_bunch(curves, head_height, hair_length, side=-1, spread=spread)
        _add_bunch(curves, head_height, hair_length, side=1, spread=spread)
    elif bunches == 1:
        _add_bunch(curves, head_height, hair_length, side=0, spread=spread * 0.5)

    # Convert all curves to mesh and join
    bpy.ops.object.select_all(action='DESELECT')
    for c in curves:
        c.select_set(True)
    if curves:
        bpy.context.view_layer.objects.active = curves[0]
        bpy.ops.object.convert(target='MESH')
        bpy.ops.object.join()

        hair = bpy.context.active_object
        hair.name = "AIMoeMaker_Hair"
        hair["aimm_type"] = "hair"

        # Apply material
        color = colors[0] if colors else "#000000"
        mat = create_material("AIMoeMaker_Hair", color)
        if hair.data.materials:
            hair.data.materials[0] = mat
        else:
            hair.data.materials.append(mat)

        bpy.ops.object.shade_smooth()
        move_to_collection(hair, "AIMoeMaker")
        set_active(hair)
        return hair

    return None


def _add_bunch(curves: list, head_height: float, hair_length: float, side: int, spread: float):
    """Add a ponytail/twintail bunch of curves."""
    bunch_count = 6
    base_x = side * 0.1 * spread
    base_z = head_height - 0.05

    for i in range(bunch_count):
        angle = (i / bunch_count) * math.pi * 0.5 - math.pi * 0.25

        start = Vector((base_x, -0.08, base_z))
        end = Vector((
            base_x + math.cos(angle) * 0.05 * side if side != 0 else 0,
            -0.1 - hair_length * 0.3,
            base_z - hair_length * 0.8
        ))
        mid = (start + end) * 0.5 + Vector((0, -0.05, 0.05))

        curve_data = bpy.data.curves.new(f"hair_bunch_{side}_{i}", 'CURVE')
        curve_data.dimensions = '3D'
        curve_data.bevel_depth = 0.01
        curve_data.bevel_resolution = 2

        spline = curve_data.splines.new('BEZIER')
        spline.bezier_points.add(2)

        for j, (pos, hl, hr) in enumerate([
            (start, start + Vector((0, 0, 0.03)), start + Vector((0, -0.03, -0.03))),
            (mid, mid + Vector((0, 0.02, 0.02)), mid + Vector((0, -0.02, -0.02))),
            (end, end + Vector((0, 0.02, 0.02)), end + Vector((0, 0, -0.01))),
        ]):
            p = spline.bezier_points[j]
            p.co = pos
            p.handle_left = hl
            p.handle_right = hr

        curve_obj = bpy.data.objects.new(f"hair_bunch_{side}_{i}", curve_data)
        bpy.context.collection.objects.link(curve_obj)
        curves.append(curve_obj)
