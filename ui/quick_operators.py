"""
Operators for Quick Panel — direct command execution without AI.
"""
import bpy
from ui.operators import get_session, get_engine
from utils.undo import push_undo


def _exec_command(action, params):
    """Execute a command via the engine and update session."""
    session = get_session()
    engine = get_engine()
    push_undo(action)
    result = engine.execute(action, params, context={"model_state": session.model_state, "bpy_available": True})
    # Log to chat history for sync
    if result.get("success"):
        session.add_message("assistant", f"[快捷面板] {result.get('message', action)}")
    return result


class AIMM_OT_ApplyBody(bpy.types.Operator):
    bl_idname = "aimm.apply_body"
    bl_label = "应用体型"
    def execute(self, context):
        scene = context.scene
        _exec_command("create_base_body", {
            "body_type": scene.aimm_body_type,
            "height": scene.aimm_body_height,
        })
        _exec_command("adjust_proportions", {
            "bust": scene.aimm_body_bust,
            "waist": scene.aimm_body_waist,
            "hip": scene.aimm_body_hip,
        })
        return {'FINISHED'}


class AIMM_OT_ApplyHair(bpy.types.Operator):
    bl_idname = "aimm.apply_hair"
    bl_label = "应用头发"
    def execute(self, context):
        scene = context.scene
        color_hex = "#{:02x}{:02x}{:02x}".format(
            int(scene.aimm_hair_color[0] * 255),
            int(scene.aimm_hair_color[1] * 255),
            int(scene.aimm_hair_color[2] * 255),
        )
        _exec_command("add_hair", {
            "style": scene.aimm_hair_style,
            "colors": [color_hex],
            "length": scene.aimm_hair_length,
            "gradient": scene.aimm_hair_gradient,
        })
        return {'FINISHED'}


class AIMM_OT_ApplyFace(bpy.types.Operator):
    bl_idname = "aimm.apply_face"
    bl_label = "应用面部"
    def execute(self, context):
        scene = context.scene
        color_hex = "#{:02x}{:02x}{:02x}".format(
            int(scene.aimm_eye_color[0] * 255),
            int(scene.aimm_eye_color[1] * 255),
            int(scene.aimm_eye_color[2] * 255),
        )
        _exec_command("set_eye_shape", {"shape": scene.aimm_eye_shape})
        _exec_command("set_eye_color", {"color": color_hex})
        _exec_command("adjust_face_shape", {"shape": scene.aimm_face_shape})
        return {'FINISHED'}


class AIMM_OT_AddClothingQuick(bpy.types.Operator):
    bl_idname = "aimm.add_clothing"
    bl_label = "添加服装"
    def execute(self, context):
        _exec_command("add_clothing", {"type": context.scene.aimm_clothing_type})
        return {'FINISHED'}


class AIMM_OT_AddAccessoryQuick(bpy.types.Operator):
    bl_idname = "aimm.add_accessory_quick"
    bl_label = "添加配饰"
    def execute(self, context):
        _exec_command("add_accessory", {"type": context.scene.aimm_accessory_type})
        return {'FINISHED'}


class AIMM_OT_SetupSkeleton(bpy.types.Operator):
    bl_idname = "aimm.setup_skeleton"
    bl_label = "配置骨骼"
    def execute(self, context):
        _exec_command("setup_skeleton", {})
        return {'FINISHED'}


class AIMM_OT_AutoWeight(bpy.types.Operator):
    bl_idname = "aimm.auto_weight"
    bl_label = "自动权重"
    def execute(self, context):
        _exec_command("auto_weight_paint", {})
        return {'FINISHED'}


class AIMM_OT_SetupHairPhysics(bpy.types.Operator):
    bl_idname = "aimm.setup_hair_physics"
    bl_label = "头发物理"
    def execute(self, context):
        _exec_command("setup_hair_physics", {})
        return {'FINISHED'}


class AIMM_OT_SetupClothPhysics(bpy.types.Operator):
    bl_idname = "aimm.setup_cloth_physics"
    bl_label = "服装物理"
    def execute(self, context):
        _exec_command("setup_cloth_physics", {"index": 0})
        return {'FINISHED'}


class AIMM_OT_AddExpressions(bpy.types.Operator):
    bl_idname = "aimm.add_expressions"
    bl_label = "添加表情集"
    def execute(self, context):
        _exec_command("add_expression_set", {"preset": "standard"})
        return {'FINISHED'}


class AIMM_OT_ValidatePmx(bpy.types.Operator):
    bl_idname = "aimm.validate_pmx"
    bl_label = "验证模型"
    def execute(self, context):
        result = _exec_command("validate_pmx", {})
        warnings = result.get("warnings", [])
        if warnings:
            self.report({'WARNING'}, f"发现{len(warnings)}个警告: " + ", ".join(warnings))
        else:
            self.report({'INFO'}, "验证通过！")
        return {'FINISHED'}


class AIMM_OT_ExportPmx(bpy.types.Operator):
    bl_idname = "aimm.export_pmx"
    bl_label = "导出PMX"
    filepath: bpy.props.StringProperty(subtype='FILE_PATH')

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        result = _exec_command("export_pmx", {"path": self.filepath})
        if result.get("success"):
            self.report({'INFO'}, result.get("message", "导出完成"))
        else:
            self.report({'ERROR'}, result.get("error", "导出失败"))
        return {'FINISHED'}


QUICK_OPERATOR_CLASSES = [
    AIMM_OT_ApplyBody, AIMM_OT_ApplyHair, AIMM_OT_ApplyFace,
    AIMM_OT_AddClothingQuick, AIMM_OT_AddAccessoryQuick,
    AIMM_OT_SetupSkeleton, AIMM_OT_AutoWeight,
    AIMM_OT_SetupHairPhysics, AIMM_OT_SetupClothPhysics,
    AIMM_OT_AddExpressions, AIMM_OT_ValidatePmx, AIMM_OT_ExportPmx,
]
