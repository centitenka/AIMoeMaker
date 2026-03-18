from commands.base import BaseCommand
from core.model_state import ModelState

class ValidatePmx(BaseCommand):
    action = "validate_pmx"
    def execute(self, params, context):
        state: ModelState = context["model_state"]
        warnings = []

        # State-level checks (work without bpy)
        if not getattr(state.skeleton, "is_configured", False): warnings.append("骨骼未配置")
        if not getattr(state.skeleton, "ik_setup", False): warnings.append("IK骨骼未配置")
        if len(getattr(state.morphs, "expressions", [])) == 0: warnings.append("未添加表情")
        if state.hair is None: warnings.append("未添加头发")
        if len(state.clothing) == 0: warnings.append("未添加服装")

        # mmd_tools check
        try:
            from pipeline.mmd_tools_compat import is_mmd_tools_available
            if not is_mmd_tools_available():
                warnings.append("mmd_tools 未安装（无法直接导出PMX，但可保存为.blend）")
        except ImportError:
            pass

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

        # Run the full 6-stage PMX export pipeline
        from pipeline.pmx_export import run_export_pipeline
        result = run_export_pipeline(path)

        if result["success"]:
            return {"success": True, "message": f"PMX 导出成功: {path}"}

        # Collect stage info for error message
        warnings = result.get("warnings", [])
        error = result.get("error", "导出失败")
        fallback = result.get("fallback_path", "")

        message = error
        if fallback:
            message += f"\n已保存 Blender 文件: {fallback}"
        if warnings:
            message += f"\n警告: {', '.join(warnings)}"

        return {"success": False, "error": message}

EXPORT_COMMANDS = [ValidatePmx, ExportPmx]
