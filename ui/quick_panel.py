"""
Quick Panel: direct property controls for model modification.
Collapsible sections for body, hair, face, clothing, accessories, skeleton, physics, morph, export.
"""
import bpy
from ui.operators import get_session, get_engine


class AIMM_PT_QuickPanel(bpy.types.Panel):
    bl_label = "AIMoeMaker 快捷面板"
    bl_idname = "AIMM_PT_QuickPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "AIMoeMaker"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        layout.label(text="通过滑块和按钮直接控制模型", icon='MODIFIER')


class AIMM_PT_QuickBody(bpy.types.Panel):
    bl_label = "身体"
    bl_idname = "AIMM_PT_QuickBody"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "AIMoeMaker"
    bl_parent_id = "AIMM_PT_QuickPanel"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        layout.prop(scene, "aimm_body_type", text="体型")
        layout.prop(scene, "aimm_body_height", text="身高(cm)")
        layout.prop(scene, "aimm_body_bust", text="胸围")
        layout.prop(scene, "aimm_body_waist", text="腰围")
        layout.prop(scene, "aimm_body_hip", text="臀围")
        layout.operator("aimm.apply_body", text="应用体型", icon='CHECKMARK')


class AIMM_PT_QuickHair(bpy.types.Panel):
    bl_label = "头发"
    bl_idname = "AIMM_PT_QuickHair"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "AIMoeMaker"
    bl_parent_id = "AIMM_PT_QuickPanel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        layout.prop(scene, "aimm_hair_style", text="发型")
        layout.prop(scene, "aimm_hair_color", text="发色")
        layout.prop(scene, "aimm_hair_length", text="长度")
        layout.prop(scene, "aimm_hair_gradient", text="渐变")
        layout.operator("aimm.apply_hair", text="应用头发", icon='CHECKMARK')


class AIMM_PT_QuickFace(bpy.types.Panel):
    bl_label = "面部"
    bl_idname = "AIMM_PT_QuickFace"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "AIMoeMaker"
    bl_parent_id = "AIMM_PT_QuickPanel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        layout.prop(scene, "aimm_eye_shape", text="眼型")
        layout.prop(scene, "aimm_eye_color", text="瞳色")
        layout.prop(scene, "aimm_face_shape", text="脸型")
        layout.operator("aimm.apply_face", text="应用面部", icon='CHECKMARK')


class AIMM_PT_QuickClothing(bpy.types.Panel):
    bl_label = "服装"
    bl_idname = "AIMM_PT_QuickClothing"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "AIMoeMaker"
    bl_parent_id = "AIMM_PT_QuickPanel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        session = get_session()
        if session.model_state.clothing:
            for i, item in enumerate(session.model_state.clothing):
                row = layout.row()
                row.label(text=f"{i}: {item.clothing_type}", icon='MOD_CLOTH')
        else:
            layout.label(text="暂无服装", icon='INFO')
        layout.prop(scene, "aimm_clothing_type", text="类型")
        layout.operator("aimm.add_clothing", text="添加服装", icon='ADD')


class AIMM_PT_QuickAccessory(bpy.types.Panel):
    bl_label = "配饰"
    bl_idname = "AIMM_PT_QuickAccessory"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "AIMoeMaker"
    bl_parent_id = "AIMM_PT_QuickPanel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        session = get_session()
        if session.model_state.accessories:
            for i, item in enumerate(session.model_state.accessories):
                row = layout.row()
                row.label(text=f"{i}: {item.accessory_type}", icon='MESH_CIRCLE')
        else:
            layout.label(text="暂无配饰", icon='INFO')
        layout.prop(context.scene, "aimm_accessory_type", text="类型")
        layout.operator("aimm.add_accessory_quick", text="添加配饰", icon='ADD')


class AIMM_PT_QuickPipeline(bpy.types.Panel):
    bl_label = "骨骼/物理/表情/导出"
    bl_idname = "AIMM_PT_QuickPipeline"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "AIMoeMaker"
    bl_parent_id = "AIMM_PT_QuickPanel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        session = get_session()
        state = session.model_state

        col = layout.column(align=True)
        col.label(text="骨骼", icon='ARMATURE_DATA')
        if state.skeleton.is_configured:
            col.label(text="已配置", icon='CHECKMARK')
        else:
            col.operator("aimm.setup_skeleton", text="配置MMD骨骼", icon='ARMATURE_DATA')

        col.separator()
        col.label(text="物理", icon='PHYSICS')
        col.operator("aimm.setup_hair_physics", text="头发物理", icon='FORCE_WIND')
        col.operator("aimm.setup_cloth_physics", text="服装物理", icon='MOD_CLOTH')

        col.separator()
        col.label(text="表情", icon='SHAPEKEY_DATA')
        col.operator("aimm.add_expressions", text="添加标准表情集", icon='ADD')
        if state.morphs.expressions:
            col.label(text=f"已有{len(state.morphs.expressions)}个表情")

        col.separator()
        col.label(text="导出", icon='EXPORT')
        col.operator("aimm.validate_pmx", text="验证模型", icon='FILE_TICK')
        col.operator("aimm.export_pmx", text="导出PMX", icon='FILE_BLANK')


QUICK_PANEL_CLASSES = [
    AIMM_PT_QuickPanel,
    AIMM_PT_QuickBody,
    AIMM_PT_QuickHair,
    AIMM_PT_QuickFace,
    AIMM_PT_QuickClothing,
    AIMM_PT_QuickAccessory,
    AIMM_PT_QuickPipeline,
]
