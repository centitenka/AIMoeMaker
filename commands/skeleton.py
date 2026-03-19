from .base import BaseCommand
from ..core.model_state import ModelState

MMD_STANDARD_BONES = ["全ての親", "センター", "グルーブ", "腰", "上半身", "上半身2", "首", "頭", "左肩", "左腕", "左ひじ", "左手首", "右肩", "右腕", "右ひじ", "右手首", "下半身", "左足", "左ひざ", "左足首", "右足", "右ひざ", "右足首", "左つま先", "右つま先", "左足ＩＫ", "右足ＩＫ", "左つま先ＩＫ", "右つま先ＩＫ"]

class SetupSkeleton(BaseCommand):
    action = "setup_skeleton"
    def execute(self, params, context):
        state: ModelState = context["model_state"]
        if context.get("bpy_available", False):
            from ..blender_ops.skeleton_ops import create_skeleton
            create_skeleton(state.body.height)
        state.skeleton.is_configured = True
        state.skeleton.ik_setup = True
        return {"success": True, "message": f"已配置MMD标准骨骼（{len(MMD_STANDARD_BONES)}根）"}

class AutoWeightPaint(BaseCommand):
    action = "auto_weight_paint"
    def execute(self, params, context):
        state: ModelState = context["model_state"]
        if not getattr(state.skeleton, "is_configured", False):
            return {"success": False, "error": "请先配置骨骼（setup_skeleton）"}
        if context.get("bpy_available", False):
            from ..blender_ops.skeleton_ops import auto_weight_paint
            auto_weight_paint(state.body.height)
        return {"success": True, "message": "自动权重绘制完成"}

SKELETON_COMMANDS = [SetupSkeleton, AutoWeightPaint]
