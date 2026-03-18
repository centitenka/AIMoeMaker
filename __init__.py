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

    ALL_CLASSES = PREFERENCE_CLASSES + OPERATOR_CLASSES + PANEL_CLASSES

def register():
    if not _bpy_available:
        return
    for cls in ALL_CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.aimm_chat_input = bpy.props.StringProperty(name="消息", description="输入消息给 AI 助手", default="")
    bpy.types.Scene.aimm_is_loading = bpy.props.BoolProperty(name="加载中", default=False)

def unregister():
    if not _bpy_available:
        return
    del bpy.types.Scene.aimm_is_loading
    del bpy.types.Scene.aimm_chat_input
    for cls in reversed(ALL_CLASSES):
        bpy.utils.unregister_class(cls)
