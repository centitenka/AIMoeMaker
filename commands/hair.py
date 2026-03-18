from commands.base import BaseCommand
from core.model_state import ModelState, HairState

HAIR_STYLES = ["short", "long", "twintail", "ponytail", "bob", "hime_cut", "drill", "braid", "odango", "ahoge"]

class AddHair(BaseCommand):
    action = "add_hair"
    def execute(self, params: dict, context: dict) -> dict:
        state: ModelState = context["model_state"]
        style = params.get("style", "short")
        colors = params.get("colors", ["#000000"])
        length = params.get("length", 0.5)
        gradient = params.get("gradient", False)
        state.hair = HairState(style=style, colors=colors if isinstance(colors, list) else [colors], length=max(0.0, min(1.0, length)), gradient=gradient, physics_enabled=True)
        if context.get("bpy_available", False):
            self._create_hair_mesh(state, context)
        return {"success": True, "message": f"已添加{style}发型"}
    def _create_hair_mesh(self, state, context):
        import bpy
        for obj in bpy.data.objects:
            if obj.get("aimm_type") == "hair":
                bpy.data.objects.remove(obj, do_unlink=True)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.15, location=(0, 0, state.body.height / 100))
        hair_obj = bpy.context.active_object
        hair_obj.name = "AIMoeMaker_Hair"
        hair_obj["aimm_type"] = "hair"

class ModifyHairStyle(BaseCommand):
    action = "modify_hair_style"
    def execute(self, params: dict, context: dict) -> dict:
        state: ModelState = context["model_state"]
        if state.hair is None:
            return {"success": False, "error": "还没有添加头发，请先使用 add_hair"}
        if "style" in params:
            state.hair.style = params["style"]
        if "length" in params:
            state.hair.length = max(0.0, min(1.0, params["length"]))
        return {"success": True, "message": f"发型已修改为{state.hair.style}"}

class SetHairColor(BaseCommand):
    action = "set_hair_color"
    def execute(self, params: dict, context: dict) -> dict:
        state: ModelState = context["model_state"]
        if state.hair is None:
            return {"success": False, "error": "还没有添加头发，请先使用 add_hair"}
        if "colors" in params:
            colors = params["colors"]
            state.hair.colors = colors if isinstance(colors, list) else [colors]
        if "gradient" in params:
            state.hair.gradient = params["gradient"]
        return {"success": True, "message": "头发颜色已更新"}

HAIR_COMMANDS = [AddHair, ModifyHairStyle, SetHairColor]
