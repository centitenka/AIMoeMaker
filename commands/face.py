from .base import BaseCommand
from ..core.model_state import ModelState, FaceState

EYE_SHAPES = ["round", "almond", "cat", "droopy", "tsurime", "tareme"]
FACE_SHAPES = ["oval", "round", "heart", "square", "diamond"]

class SetEyeShape(BaseCommand):
    action = "set_eye_shape"
    def execute(self, params: dict, context: dict) -> dict:
        state: ModelState = context["model_state"]
        if state.face is None:
            state.face = FaceState()
        shape = params.get("shape", "round")
        state.face.eye_shape = shape
        if context.get("bpy_available", False):
            from ..blender_ops.face_ops import create_eyes
            from ..blender_ops.utils import find_aimm_object
            body = find_aimm_object("body")
            if body:
                head_z = body.get("aimm_height", 158.0) / 100.0 * 0.92
                head_r = body.get("aimm_height", 158.0) / 100.0 / 7.0 * 0.45
                eye_color = state.face.eye_color if state.face else "#663300"
                create_eyes(shape, eye_color, head_z, head_r)
        return {"success": True, "message": f"眼型已设置为{shape}"}

class SetEyeColor(BaseCommand):
    action = "set_eye_color"
    def execute(self, params: dict, context: dict) -> dict:
        state: ModelState = context["model_state"]
        if state.face is None:
            state.face = FaceState()
        color = params.get("color", "#663300")
        state.face.eye_color = color
        if context.get("bpy_available", False):
            from ..blender_ops.face_ops import update_eye_color
            update_eye_color(color)
        return {"success": True, "message": f"瞳色已设置为{color}"}

class AdjustFaceShape(BaseCommand):
    action = "adjust_face_shape"
    def execute(self, params: dict, context: dict) -> dict:
        state: ModelState = context["model_state"]
        if state.face is None:
            state.face = FaceState()
        shape = params.get("shape", "oval")
        state.face.face_shape = shape
        return {"success": True, "message": f"脸型已调整为{shape}"}

FACE_COMMANDS = [SetEyeShape, SetEyeColor, AdjustFaceShape]
