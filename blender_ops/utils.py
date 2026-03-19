"""
Shared utilities for Blender 3D operations.
All functions in this module require bpy to be available.
"""


def find_aimm_object(aimm_type: str):
    """Find the first object with the given aimm_type custom property."""
    import bpy
    for obj in bpy.data.objects:
        if obj.get("aimm_type") == aimm_type:
            return obj
    return None


def find_all_aimm_objects(aimm_type: str) -> list:
    """Find all objects with the given aimm_type."""
    import bpy
    return [obj for obj in bpy.data.objects if obj.get("aimm_type") == aimm_type]


def remove_aimm_objects(aimm_type: str):
    """Remove all objects with the given aimm_type from the scene.

    Before removing, orphans any children so they remain in the scene.
    """
    import bpy
    objects = find_all_aimm_objects(aimm_type)
    for obj in objects:
        # Reparent children to this object's parent (or unparent)
        for child in list(obj.children):
            child.parent = obj.parent
        # Remove mesh/curve data too
        data = obj.data
        bpy.data.objects.remove(obj, do_unlink=True)
        if data and data.users == 0:
            if hasattr(bpy.data, 'meshes') and isinstance(data, bpy.types.Mesh):
                bpy.data.meshes.remove(data)
            elif hasattr(bpy.data, 'curves') and isinstance(data, bpy.types.Curve):
                bpy.data.curves.remove(data)


def reparent_aimm_children(new_parent_obj):
    """Re-parent all orphaned AIMoeMaker objects to new_parent_obj.

    Called after body recreation to restore parent-child relationships
    for hair, eyes, clothing, etc.
    """
    import bpy
    child_types = ("hair", "eye", "clothing", "accessory")
    for obj in bpy.data.objects:
        aimm_type = obj.get("aimm_type")
        if aimm_type in child_types and obj.parent is None and obj != new_parent_obj:
            obj.parent = new_parent_obj


def create_material(name: str, color_hex: str) -> "bpy.types.Material":
    """Create or get a material with the given name and base color."""
    import bpy
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True

    # Set base color from hex
    r, g, b = hex_to_rgb(color_hex)
    if mat.use_nodes:
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (r, g, b, 1.0)

    return mat


def hex_to_rgb(hex_color: str) -> tuple[float, float, float]:
    """Convert hex color string to (r, g, b) floats in 0-1 range."""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) != 6:
        return (0.5, 0.5, 0.5)
    try:
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0
        return (r, g, b)
    except ValueError:
        return (0.5, 0.5, 0.5)


def ensure_collection(name: str) -> "bpy.types.Collection":
    """Get or create a collection for organizing AIMoeMaker objects."""
    import bpy
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    return col


def move_to_collection(obj, collection_name: str):
    """Move an object to a specific collection."""
    import bpy
    col = ensure_collection(collection_name)
    # Unlink from all current collections
    for c in obj.users_collection:
        c.objects.unlink(obj)
    col.objects.link(obj)


def set_active(obj):
    """Set object as active and selected."""
    import bpy
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
