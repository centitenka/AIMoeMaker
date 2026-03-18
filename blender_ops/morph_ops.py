# blender_ops/morph_ops.py
"""
Shape key (morph) creation for MMD facial expressions.
"""
import bpy
from blender_ops.utils import find_aimm_object


# Standard MMD expression definitions
# Each expression defines which shape key it creates and basic deformation hints
EXPRESSION_CATEGORIES = {
    "eyebrow": ["真面目", "困る", "にこり", "怒り", "上", "下"],
    "eye": ["まばたき", "笑い", "ウィンク", "ウィンク右", "ウィンク２"],
    "mouth": ["あ", "い", "う", "え", "お", "△", "∧", "ω"],
    "other": ["照れ"],
}


def create_morph(name: str, category: str = "other"):
    """
    Create a single shape key (morph) on the body mesh.

    Args:
        name: Shape key name (typically Japanese)
        category: Category for MMD display frame
    """
    body = find_aimm_object("body")
    if body is None or body.type != 'MESH':
        return False

    # Ensure basis shape key exists
    if body.data.shape_keys is None:
        body.shape_key_add(name="Basis")

    # Check if shape key already exists
    if name in [sk.name for sk in body.data.shape_keys.key_blocks]:
        return True  # Already exists

    # Add new shape key
    sk = body.shape_key_add(name=name)
    sk.value = 0.0

    # Apply basic deformation based on category and name
    _apply_expression_deform(body, sk, name, category)

    return True


def add_expression_set(preset: str = "standard"):
    """
    Add a full set of standard MMD expressions as shape keys.

    Args:
        preset: Expression set name ("standard" is the only one currently)
    """
    body = find_aimm_object("body")
    if body is None or body.type != 'MESH':
        return False

    # Ensure basis exists
    if body.data.shape_keys is None:
        body.shape_key_add(name="Basis")

    created = 0
    for category, expressions in EXPRESSION_CATEGORIES.items():
        for expr_name in expressions:
            if expr_name not in [sk.name for sk in body.data.shape_keys.key_blocks]:
                sk = body.shape_key_add(name=expr_name)
                sk.value = 0.0
                _apply_expression_deform(body, sk, expr_name, category)
                created += 1

    return created


def _apply_expression_deform(body, shape_key, name: str, category: str):
    """
    Apply basic deformation to shape key based on expression type.

    For now, this creates placeholder deformations. In production,
    these would be more sophisticated facial deformations.
    """
    if body.data.shape_keys is None:
        return

    basis = body.data.shape_keys.key_blocks["Basis"]
    sk_data = shape_key.data

    # Get approximate head vertex range (top portion of mesh)
    # This is a simplified approach - in production you'd use vertex groups
    mesh = body.data
    max_z = max(v.co.z for v in mesh.vertices)
    head_threshold = max_z * 0.85  # Top 15% of mesh is roughly the head

    for i, vert in enumerate(mesh.vertices):
        if vert.co.z > head_threshold:
            base = basis.data[i].co.copy()

            if category == "eye":
                if "まばたき" in name or "ウィンク" in name:
                    # Close eyes - move eye-area vertices slightly inward
                    if abs(vert.co.z - max_z * 0.92) < max_z * 0.02:
                        base.y += 0.002
                        base.z -= 0.001
                elif "笑い" in name:
                    if abs(vert.co.z - max_z * 0.92) < max_z * 0.02:
                        base.z -= 0.002

            elif category == "mouth":
                if vert.co.z < max_z * 0.88 and vert.co.z > max_z * 0.84:
                    if name in ("あ", "お"):
                        base.z -= 0.003
                    elif name in ("い", "え"):
                        base.x *= 1.02
                    elif name == "う":
                        base.y -= 0.002

            elif category == "eyebrow":
                if vert.co.z > max_z * 0.95:
                    if "上" in name:
                        base.z += 0.002
                    elif "下" in name or "困" in name:
                        base.z -= 0.002
                    elif "怒" in name:
                        base.z -= 0.001
                        base.x *= 0.98

            elif category == "other":
                if "照れ" in name:
                    # Blush - slight outward push on cheeks
                    if max_z * 0.88 < vert.co.z < max_z * 0.92:
                        if abs(vert.co.x) > 0.02:
                            base.y -= 0.001

            sk_data[i].co = base
