"""
Quick Panel: direct manipulation UI with sliders, dropdowns, and buttons.
Alternative to chat-based interaction.
"""
import bpy
from .operators import get_session, get_engine


# --- Property Update Callbacks ---

def _on_body_type_update(self, context):
    session = get_session()
    engine = get_engine()
    body_type = self.aimm_body_type
    engine.execute("create_base_body", {"body_type": body_type}, {"model_state": session.model_state, "bpy_available": True})
    _tag_redraw(context)


def _on_height_update(self, context):
    session = get_session()
    engine = get_engine()
    engine.execute("set_height", {"height": self.aimm_height}, {"model_state": session.model_state, "bpy_available": True})
    _tag_redraw(context)


def _on_hair_style_update(self, context):
    session = get_session()
    engine = get_engine()
    if session.model_state.hair is None:
        engine.execute("add_hair", {"style": self.aimm_hair_style}, {"model_state": session.model_state, "bpy_available": True})
    else:
        engine.execute("modify_hair_style", {"style": self.aimm_hair_style}, {"model_state": session.model_state, "bpy_available": True})
    _tag_redraw(context)


def _on_eye_shape_update(self, context):
    session = get_session()
    engine = get_engine()
    engine.execute("set_eye_shape", {"shape": self.aimm_eye_shape}, {"model_state": session.model_state, "bpy_available": True})
    _tag_redraw(context)


def _on_face_shape_update(self, context):
    session = get_session()
    engine = get_engine()
    engine.execute("adjust_face_shape", {"shape": self.aimm_face_shape}, {"model_state": session.model_state, "bpy_available": True})
    _tag_redraw(context)


def _tag_redraw(context):
    for area in context.screen.areas:
        if area.type == 'VIEW_3D':
            area.tag_redraw()


# --- Panels ---

class AIMM_PT_QuickPanel(bpy.types.Panel):
    bl_label = "快捷面板"
    bl_idname = "AIMM_PT_QuickPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "AIMoeMaker"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        layout.label(text="直接调整模型参数", icon='MODIFIER')


class AIMM_PT_QP_Body(bpy.types.Panel):
    bl_label = "身体"
    bl_idname = "AIMM_PT_QP_Body"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "AIMoeMaker"
    bl_parent_id = "AIMM_PT_QuickPanel"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        layout.prop(scene, "aimm_body_type", text="体型")
        layout.prop(scene, "aimm_height", text="身高 (cm)")
        col = layout.column(align=True)
        col.label(text="身体比例:")
        col.prop(scene, "aimm_bust", text="胸围", slider=True)
        col.prop(scene, "aimm_waist", text="腰围", slider=True)
        col.prop(scene, "aimm_hip", text="臀围", slider=True)


class AIMM_PT_QP_Hair(bpy.types.Panel):
    bl_label = "头发"
    bl_idname = "AIMM_PT_QP_Hair"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "AIMoeMaker"
    bl_parent_id = "AIMM_PT_QuickPanel"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        layout.prop(scene, "aimm_hair_style", text="发型")
        layout.prop(scene, "aimm_hair_color", text="发色")
        layout.prop(scene, "aimm_hair_length", text="长度", slider=True)


class AIMM_PT_QP_Face(bpy.types.Panel):
    bl_label = "面部"
    bl_idname = "AIMM_PT_QP_Face"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "AIMoeMaker"
    bl_parent_id = "AIMM_PT_QuickPanel"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        layout.prop(scene, "aimm_eye_shape", text="眼型")
        layout.prop(scene, "aimm_eye_color", text="瞳色")
        layout.prop(scene, "aimm_face_shape", text="脸型")


class AIMM_PT_QP_Advanced(bpy.types.Panel):
    bl_label = "骨骼/物理/表情/导出"
    bl_idname = "AIMM_PT_QP_Advanced"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "AIMoeMaker"
    bl_parent_id = "AIMM_PT_QuickPanel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.label(text="骨骼:", icon='ARMATURE_DATA')
        row = col.row(align=True)
        row.operator("aimm.setup_skeleton")
        row.operator("aimm.auto_weight")

        col.separator()
        col.label(text="表情:", icon='SHAPEKEY_DATA')
        col.operator("aimm.add_expressions")

        col.separator()
        col.label(text="导出:", icon='EXPORT')
        row = col.row(align=True)
        row.operator("aimm.validate_pmx")
        row.operator("aimm.export_pmx")


QUICK_PANEL_CLASSES = [
    AIMM_PT_QuickPanel,
    AIMM_PT_QP_Body,
    AIMM_PT_QP_Hair,
    AIMM_PT_QP_Face,
    AIMM_PT_QP_Advanced,
]
