from commands.base import BaseCommand
from core.model_state import ModelState

class SetupHairPhysics(BaseCommand):
    action = "setup_hair_physics"
    def execute(self, params, context):
        state: ModelState = context["model_state"]
        if state.hair is None:
            return {"success": False, "error": "还没有添加头发，请先使用 add_hair"}
        state.hair.physics_enabled = True
        state.physics.rigid_body_count = getattr(state.physics, "rigid_body_count", 0) + 10
        state.physics.joint_count = getattr(state.physics, "joint_count", 0) + 9
        return {"success": True, "message": "头发物理已配置"}

class SetupClothPhysics(BaseCommand):
    action = "setup_cloth_physics"
    def execute(self, params, context):
        state: ModelState = context["model_state"]
        index = params.get("index", 0)
        if index < 0 or index >= len(state.clothing):
            return {"success": False, "error": f"服装索引{index}无效"}
        state.clothing[index].physics_enabled = True
        state.physics.rigid_body_count = getattr(state.physics, "rigid_body_count", 0) + 8
        state.physics.joint_count = getattr(state.physics, "joint_count", 0) + 7
        return {"success": True, "message": "服装物理已配置"}

PHYSICS_COMMANDS = [SetupHairPhysics, SetupClothPhysics]
