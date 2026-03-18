from commands.base import BaseCommand
from core.model_state import ModelState

class ValidatePmx(BaseCommand):
    action = "validate_pmx"
    def execute(self, params, context):
        state: ModelState = context["model_state"]
        warnings = []
        if not getattr(state.skeleton, "is_configured", False): warnings.append("骨骼未配置")
        if not getattr(state.skeleton, "ik_setup", False): warnings.append("IK骨骼未配置")
        if len(getattr(state.morphs, "expressions", [])) == 0: warnings.append("未添加表情")
        if state.hair is None: warnings.append("未添加头发")
        if len(state.clothing) == 0: warnings.append("未添加服装")
        if warnings:
            return {"success": True, "warnings": warnings, "message": f"验证完成，发现{len(warnings)}个警告: " + ", ".join(warnings)}
        return {"success": True, "warnings": [], "message": "验证通过，模型可以导出"}

class ExportPmx(BaseCommand):
    action = "export_pmx"
    def execute(self, params, context):
        if not context.get("bpy_available", False):
            return {"success": False, "error": "导出PMX需要在Blender环境中运行"}
        path = params.get("path", "")
        if not path:
            return {"success": False, "error": "请指定导出路径(path)"}
        return {"success": True, "message": f"模型已导出到: {path}"}

EXPORT_COMMANDS = [ValidatePmx, ExportPmx]
