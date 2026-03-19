from .base import BaseCommand
from ..core.model_state import ModelState, ClothingItem

class AddClothing(BaseCommand):
    action = "add_clothing"
    def execute(self, params: dict, context: dict) -> dict:
        state: ModelState = context["model_state"]
        clothing_type = params.get("type", "generic")
        color = params.get("color", "#FFFFFF")
        material = params.get("material", "")
        physics = params.get("physics_enabled", False)
        item = ClothingItem(clothing_type=clothing_type, color=color, material=material, physics_enabled=physics)
        state.clothing.append(item)
        if context.get("bpy_available", False):
            from ..blender_ops.clothing_ops import create_clothing
            idx = len(state.clothing) - 1
            create_clothing(clothing_type, color, state.body.height if hasattr(state, 'body') else 158.0, idx)
        return {"success": True, "message": f"已添加服装: {clothing_type}"}

class ModifyClothing(BaseCommand):
    action = "modify_clothing"
    def execute(self, params: dict, context: dict) -> dict:
        state: ModelState = context["model_state"]
        index = params.get("index", 0)
        if index < 0 or index >= len(state.clothing):
            return {"success": False, "error": f"服装索引{index}无效，当前共{len(state.clothing)}件服装"}
        item = state.clothing[index]
        if "color" in params: item.color = params["color"]
        if "type" in params: item.clothing_type = params["type"]
        if "material" in params: item.material = params["material"]
        if "physics_enabled" in params: item.physics_enabled = params["physics_enabled"]
        if context.get("bpy_available", False) and "color" in params:
            from ..blender_ops.clothing_ops import update_clothing_color
            update_clothing_color(index, item.color)
        return {"success": True, "message": "服装已修改"}

class SetFabricMaterial(BaseCommand):
    action = "set_fabric_material"
    def execute(self, params: dict, context: dict) -> dict:
        state: ModelState = context["model_state"]
        index = params.get("index", 0)
        if index < 0 or index >= len(state.clothing):
            return {"success": False, "error": f"服装索引{index}无效"}
        item = state.clothing[index]
        if "material" in params: item.material = params["material"]
        if "physics_enabled" in params: item.physics_enabled = params["physics_enabled"]
        return {"success": True, "message": f"面料材质已设置为{item.material}"}

CLOTHING_COMMANDS = [AddClothing, ModifyClothing, SetFabricMaterial]
