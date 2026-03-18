# bl_info is a fallback for manual .zip installation.
# When installed via Extensions Platform, blender_manifest.toml takes precedence.
bl_info = {
    "name": "AIMoeMaker",
    "author": "AIMoeMaker Team",
    "version": (0, 1, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > AIMoeMaker",
    "description": "AI驱动的MMD建模助手，通过自然语言对话创建MMD模型",
    "category": "3D View",
}

try:
    import bpy
    _bpy_available = True
except ImportError:
    _bpy_available = False

if _bpy_available:
    from ui.preferences import PREFERENCE_CLASSES
    from ui.operators import OPERATOR_CLASSES
    from ui.chat_panel import PANEL_CLASSES
    from ui.quick_panel import (
        QUICK_PANEL_CLASSES,
        _on_body_type_update,
        _on_height_update,
        _on_hair_style_update,
        _on_eye_shape_update,
        _on_face_shape_update,
    )
    from ui.quick_operators import QUICK_OPERATOR_CLASSES
    from ui.node_view import NODE_TREE_CLASSES, register_node_categories, unregister_node_categories
    from ui.node_nodes import ALL_NODE_CLASSES, NODE_ITEMS_BY_CATEGORY
    from ui.node_eval import NODE_EVAL_CLASSES
    from ui.node_header import draw_aimm_node_header

    ALL_CLASSES = PREFERENCE_CLASSES + OPERATOR_CLASSES + PANEL_CLASSES + QUICK_PANEL_CLASSES + QUICK_OPERATOR_CLASSES + NODE_TREE_CLASSES + ALL_NODE_CLASSES + NODE_EVAL_CLASSES

def register():
    if not _bpy_available:
        return
    for cls in ALL_CLASSES:
        bpy.utils.register_class(cls)
    register_node_categories(ALL_NODE_CLASSES, NODE_ITEMS_BY_CATEGORY)
    bpy.types.NODE_HT_header.append(draw_aimm_node_header)
    bpy.types.Scene.aimm_chat_input = bpy.props.StringProperty(name="消息", description="输入消息给 AI 助手", default="")
    bpy.types.Scene.aimm_is_loading = bpy.props.BoolProperty(name="加载中", default=False)

    # Body
    bpy.types.Scene.aimm_body_type = bpy.props.EnumProperty(
        name="体型", items=[("loli", "萝莉", ""), ("teen", "少女", ""), ("default", "默认", ""), ("adult", "成人", "")],
        default="default", update=_on_body_type_update)
    bpy.types.Scene.aimm_body_height = bpy.props.FloatProperty(name="身高", default=158.0, min=50.0, max=300.0, subtype='DISTANCE')
    bpy.types.Scene.aimm_body_bust = bpy.props.FloatProperty(name="胸围", default=0.5, min=0.0, max=1.0, subtype='FACTOR')
    bpy.types.Scene.aimm_body_waist = bpy.props.FloatProperty(name="腰围", default=0.5, min=0.0, max=1.0, subtype='FACTOR')
    bpy.types.Scene.aimm_body_hip = bpy.props.FloatProperty(name="臀围", default=0.5, min=0.0, max=1.0, subtype='FACTOR')
    # Quick panel short-name properties (with update callbacks)
    bpy.types.Scene.aimm_height = bpy.props.FloatProperty(
        name="身高", default=158.0, min=50.0, max=300.0, update=_on_height_update)
    bpy.types.Scene.aimm_bust = bpy.props.FloatProperty(name="胸围", default=0.5, min=0.0, max=1.0)
    bpy.types.Scene.aimm_waist = bpy.props.FloatProperty(name="腰围", default=0.5, min=0.0, max=1.0)
    bpy.types.Scene.aimm_hip = bpy.props.FloatProperty(name="臀围", default=0.5, min=0.0, max=1.0)

    # Hair
    bpy.types.Scene.aimm_hair_style = bpy.props.EnumProperty(
        name="发型", items=[("short", "短发", ""), ("long", "长发", ""), ("twintail", "双马尾", ""), ("ponytail", "马尾", ""), ("bob", "波波头", ""), ("hime_cut", "公主切", ""), ("braid", "辫子", ""), ("odango", "丸子头", "")],
        default="short", update=_on_hair_style_update)
    bpy.types.Scene.aimm_hair_color = bpy.props.FloatVectorProperty(name="发色", subtype='COLOR', default=(0.0, 0.0, 0.0), min=0.0, max=1.0)
    bpy.types.Scene.aimm_hair_length = bpy.props.FloatProperty(name="长度", default=0.5, min=0.0, max=1.0, subtype='FACTOR')
    bpy.types.Scene.aimm_hair_gradient = bpy.props.BoolProperty(name="渐变", default=False)

    # Face
    bpy.types.Scene.aimm_eye_shape = bpy.props.EnumProperty(
        name="眼型", items=[("round", "圆形", ""), ("almond", "杏仁", ""), ("cat", "猫眼", ""), ("droopy", "下垂", ""), ("tsurime", "吊眼", ""), ("tareme", "垂眼", "")],
        default="round", update=_on_eye_shape_update)
    bpy.types.Scene.aimm_eye_color = bpy.props.FloatVectorProperty(name="瞳色", subtype='COLOR', default=(0.4, 0.2, 0.0), min=0.0, max=1.0)
    bpy.types.Scene.aimm_face_shape = bpy.props.EnumProperty(
        name="脸型", items=[("oval", "椭圆", ""), ("round", "圆形", ""), ("heart", "心形", ""), ("square", "方形", ""), ("diamond", "菱形", "")],
        default="oval", update=_on_face_shape_update)

    # Clothing & Accessory
    bpy.types.Scene.aimm_clothing_type = bpy.props.StringProperty(name="服装类型", default="dress")
    bpy.types.Scene.aimm_accessory_type = bpy.props.StringProperty(name="配饰类型", default="ribbon")

def unregister():
    if not _bpy_available:
        return
    bpy.types.NODE_HT_header.remove(draw_aimm_node_header)
    unregister_node_categories()
    del bpy.types.Scene.aimm_accessory_type
    del bpy.types.Scene.aimm_clothing_type
    del bpy.types.Scene.aimm_face_shape
    del bpy.types.Scene.aimm_eye_color
    del bpy.types.Scene.aimm_eye_shape
    del bpy.types.Scene.aimm_hair_gradient
    del bpy.types.Scene.aimm_hair_length
    del bpy.types.Scene.aimm_hair_color
    del bpy.types.Scene.aimm_hair_style
    del bpy.types.Scene.aimm_hip
    del bpy.types.Scene.aimm_waist
    del bpy.types.Scene.aimm_bust
    del bpy.types.Scene.aimm_height
    del bpy.types.Scene.aimm_body_hip
    del bpy.types.Scene.aimm_body_waist
    del bpy.types.Scene.aimm_body_bust
    del bpy.types.Scene.aimm_body_height
    del bpy.types.Scene.aimm_body_type
    del bpy.types.Scene.aimm_is_loading
    del bpy.types.Scene.aimm_chat_input
    for cls in reversed(ALL_CLASSES):
        bpy.utils.unregister_class(cls)
