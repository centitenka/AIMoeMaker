# blender_ops/hair_ops.py
"""
Improved procedural hair generation with layers, volume, and natural flow.
Creates anime-style hair using layered Bezier curves with ribbon profiles.
"""
import bpy
import math
import random
from mathutils import Vector
from blender_ops.utils import (
    remove_aimm_objects, find_aimm_object, create_material,
    move_to_collection, set_active
)


# Style configs: (front_strands, side_strands, back_strands, length_mult, curve_strength)
HAIR_CONFIGS = {
    "short":     {"front": 8,  "side": 6,  "back": 10, "length": 0.3,  "curve": 0.15, "bunches": 0},
    "long":      {"front": 10, "side": 8,  "back": 14, "length": 1.0,  "curve": 0.4,  "bunches": 0},
    "twintail":  {"front": 10, "side": 6,  "back": 8,  "length": 0.8,  "curve": 0.3,  "bunches": 2},
    "ponytail":  {"front": 10, "side": 6,  "back": 6,  "length": 0.7,  "curve": 0.35, "bunches": 1},
    "bob":       {"front": 10, "side": 8,  "back": 12, "length": 0.35, "curve": 0.2,  "bunches": 0},
    "hime_cut":  {"front": 8,  "side": 12, "back": 12, "length": 0.9,  "curve": 0.3,  "bunches": 0},
    "drill":     {"front": 8,  "side": 6,  "back": 8,  "length": 0.7,  "curve": 0.5,  "bunches": 2},
    "braid":     {"front": 8,  "side": 6,  "back": 6,  "length": 0.6,  "curve": 0.35, "bunches": 1},
    "odango":    {"front": 8,  "side": 6,  "back": 8,  "length": 0.4,  "curve": 0.2,  "bunches": 2},
    "ahoge":     {"front": 10, "side": 6,  "back": 10, "length": 0.35, "curve": 0.15, "bunches": 0},
}


def create_hair(style: str, colors: list[str], length: float, gradient: bool, head_height: float):
    """Create layered anime-style hair."""
    remove_aimm_objects("hair")

    config = HAIR_CONFIGS.get(style, HAIR_CONFIGS["short"])
    length_mult = config["length"] * (0.5 + length * 0.5)
    curve_str = config["curve"]

    head_r = head_height / 7.0 * 0.45  # Approximate head radius
    head_z = head_height * 0.92  # Head center Z
    hair_length = head_r * 4.0 * length_mult

    seed = hash(style) % 10000
    rng = random.Random(seed)  # Deterministic randomness per style

    all_curves = []

    # Layer 1: Front bangs
    _create_hair_layer(
        all_curves, config["front"], head_z, head_r, hair_length * 0.4,
        angle_start=-0.8, angle_end=0.8, y_bias=-1.0,
        z_start_offset=0.3, curve_strength=curve_str * 0.5, rng=rng,
        bevel_depth=0.006,
    )

    # Layer 2: Side hair
    for side in [-1, 1]:
        _create_hair_layer(
            all_curves, config["side"] // 2, head_z, head_r, hair_length * 0.7,
            angle_start=side * 0.6, angle_end=side * 1.5, y_bias=-0.3,
            z_start_offset=0.2, curve_strength=curve_str * 0.8, rng=rng,
            bevel_depth=0.008,
        )

    # Layer 3: Back hair (main volume)
    _create_hair_layer(
        all_curves, config["back"], head_z, head_r, hair_length,
        angle_start=0.8, angle_end=2 * math.pi - 0.8, y_bias=0.3,
        z_start_offset=0.35, curve_strength=curve_str, rng=rng,
        bevel_depth=0.010,
    )

    # Layer 4: Bunches (twintail/ponytail)
    bunches = config["bunches"]
    if bunches == 2:
        for side in [-1, 1]:
            _create_bunch(all_curves, head_z, head_r, hair_length * 0.9,
                          x_offset=side * head_r * 0.8, rng=rng, strand_count=8)
    elif bunches == 1:
        _create_bunch(all_curves, head_z, head_r, hair_length * 0.85,
                      x_offset=0, rng=rng, strand_count=10)

    # Ahoge (hair antenna)
    if style == "ahoge":
        _create_ahoge(all_curves, head_z, head_r)

    if not all_curves:
        return None

    # Convert all curves to mesh and join
    bpy.ops.object.select_all(action='DESELECT')
    for c in all_curves:
        c.select_set(True)
    bpy.context.view_layer.objects.active = all_curves[0]
    bpy.ops.object.convert(target='MESH')
    bpy.ops.object.join()

    hair = bpy.context.active_object
    hair.name = "AIMoeMaker_Hair"
    hair["aimm_type"] = "hair"

    # Material
    color = colors[0] if colors else "#000000"
    mat = create_material("AIMoeMaker_Hair", color)
    # Make hair slightly translucent for anime look
    if mat.use_nodes:
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Roughness"].default_value = 0.4
            bsdf.inputs["Specular IOR Level"].default_value = 0.6

    if hair.data.materials:
        hair.data.materials[0] = mat
    else:
        hair.data.materials.append(mat)

    bpy.ops.object.shade_smooth()

    # Parent to body
    body = find_aimm_object("body")
    if body:
        hair.parent = body

    move_to_collection(hair, "AIMoeMaker")
    set_active(hair)
    return hair


def _create_hair_layer(curves_list, count, head_z, head_r, length,
                       angle_start, angle_end, y_bias, z_start_offset,
                       curve_strength, rng, bevel_depth):
    """Create a layer of hair strands covering an arc around the head."""
    for i in range(count):
        t = i / max(count - 1, 1)
        angle = angle_start + t * (angle_end - angle_start)

        # Add slight randomness
        angle += rng.uniform(-0.1, 0.1)
        length_var = length * rng.uniform(0.85, 1.15)

        # Start position on scalp
        sx = math.sin(angle) * head_r * 0.95
        sy = math.cos(angle) * head_r * 0.95 * (0.8 + y_bias * 0.2)
        sz = head_z + head_r * z_start_offset

        # End position (hair falls down with gravity + spread)
        spread = 1.0 + length_var * 0.3
        ex = sx * spread + rng.uniform(-0.01, 0.01)
        ey = sy * spread * 0.8 + rng.uniform(-0.005, 0.005)
        ez = sz - length_var * (0.6 + curve_strength)

        # Control points for natural curve
        m1x = sx * 1.05
        m1y = sy * 1.05
        m1z = sz - length_var * 0.25

        m2x = (sx + ex) * 0.5
        m2y = (sy + ey) * 0.5
        m2z = (sz + ez) * 0.5 + length_var * 0.05

        # Create Bezier curve
        curve_data = bpy.data.curves.new(f"hair_{len(curves_list)}", 'CURVE')
        curve_data.dimensions = '3D'
        curve_data.bevel_depth = bevel_depth
        curve_data.bevel_resolution = 2

        # Taper: thicker at root, thinner at tip
        curve_data.taper_radius_mode = 'OVERRIDE'

        spline = curve_data.splines.new('BEZIER')
        spline.bezier_points.add(3)  # 4 points total

        points = [
            (Vector((sx, sy, sz)), 0.08),      # Root - wide
            (Vector((m1x, m1y, m1z)), 0.06),   # Near root
            (Vector((m2x, m2y, m2z)), 0.04),   # Middle
            (Vector((ex, ey, ez)), 0.01),       # Tip - thin
        ]

        for j, (pos, _) in enumerate(points):
            bp = spline.bezier_points[j]
            bp.co = pos
            bp.handle_type = 'AUTO'
            bp.radius = points[j][1] / bevel_depth  # Taper via radius

        curve_obj = bpy.data.objects.new(f"hair_{len(curves_list)}", curve_data)
        bpy.context.collection.objects.link(curve_obj)
        curves_list.append(curve_obj)


def _create_bunch(curves_list, head_z, head_r, length, x_offset, rng, strand_count=8):
    """Create a ponytail/twintail bunch."""
    base_y = head_r * 0.7  # Behind the head
    base_z = head_z - head_r * 0.2

    for i in range(strand_count):
        angle = (i / strand_count) * math.pi * 2
        r_var = rng.uniform(0.01, 0.03)

        sx = x_offset + math.cos(angle) * r_var
        sy = base_y + math.sin(angle) * r_var
        sz = base_z

        # Bunch hangs down with some sway
        ex = sx + rng.uniform(-0.02, 0.02)
        ey = sy + length * 0.1
        ez = sz - length * 0.85

        mx = (sx + ex) * 0.5
        my = (sy + ey) * 0.5 + 0.02
        mz = (sz + ez) * 0.5

        curve_data = bpy.data.curves.new(f"bunch_{len(curves_list)}", 'CURVE')
        curve_data.dimensions = '3D'
        curve_data.bevel_depth = 0.012
        curve_data.bevel_resolution = 3

        spline = curve_data.splines.new('BEZIER')
        spline.bezier_points.add(2)

        for j, (pos, rad) in enumerate([
            (Vector((sx, sy, sz)), 1.2),
            (Vector((mx, my, mz)), 0.8),
            (Vector((ex, ey, ez)), 0.3),
        ]):
            bp = spline.bezier_points[j]
            bp.co = pos
            bp.handle_type = 'AUTO'
            bp.radius = rad

        curve_obj = bpy.data.objects.new(f"bunch_{len(curves_list)}", curve_data)
        bpy.context.collection.objects.link(curve_obj)
        curves_list.append(curve_obj)


def _create_ahoge(curves_list, head_z, head_r):
    """Create a single ahoge (hair antenna) strand."""
    curve_data = bpy.data.curves.new("ahoge", 'CURVE')
    curve_data.dimensions = '3D'
    curve_data.bevel_depth = 0.004
    curve_data.bevel_resolution = 2

    spline = curve_data.splines.new('BEZIER')
    spline.bezier_points.add(2)

    sz = head_z + head_r * 0.4
    points = [
        (Vector((0, -head_r * 0.3, sz)), 1.5),
        (Vector((0.02, -head_r * 0.5, sz + head_r * 0.5)), 1.0),
        (Vector((-0.01, -head_r * 0.2, sz + head_r * 0.7)), 0.3),
    ]

    for j, (pos, rad) in enumerate(points):
        bp = spline.bezier_points[j]
        bp.co = pos
        bp.handle_type = 'AUTO'
        bp.radius = rad

    curve_obj = bpy.data.objects.new("ahoge", curve_data)
    bpy.context.collection.objects.link(curve_obj)
    curves_list.append(curve_obj)
