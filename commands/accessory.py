from commands.base import BaseCommand
from core.model_state import ModelState, AccessoryItem

class AddAccessory(BaseCommand):
    action = "add_accessory"
    def execute(self, params: dict, context: dict) -> dict:
        state: ModelState = context["model_state"]
        acc_type = params.get("type", "generic")
        position = params.get("position", [0.0, 0.0, 0.0])
        scale = params.get("scale", 1.0)
        item = AccessoryItem(accessory_type=acc_type, position=position, scale=scale)
        state.accessories.append(item)
        return {"success": True, "message": f"已添加配饰: {acc_type}"}

class RemoveAccessory(BaseCommand):
    action = "remove_accessory"
    def execute(self, params: dict, context: dict) -> dict:
        state: ModelState = context["model_state"]
        if "index" in params:
            index = params["index"]
            if 0 <= index < len(state.accessories):
                removed = state.accessories.pop(index)
                return {"success": True, "message": f"已移除配饰: {removed.accessory_type}"}
            return {"success": False, "error": f"配饰索引{index}无效"}
        if "type" in params:
            acc_type = params["type"]
            for i, acc in enumerate(state.accessories):
                if acc.accessory_type == acc_type:
                    state.accessories.pop(i)
                    return {"success": True, "message": f"已移除配饰: {acc_type}"}
            return {"success": False, "error": f"未找到类型为{acc_type}的配饰"}
        return {"success": False, "error": "请指定要移除的配饰索引(index)或类型(type)"}

ACCESSORY_COMMANDS = [AddAccessory, RemoveAccessory]
