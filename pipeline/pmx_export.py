# pipeline/pmx_export.py
"""
Stage 6: PMX file export.
Orchestrates the full pipeline and calls mmd_tools for final export.
"""
from ..blender_ops.utils import find_aimm_object


def run_export_pipeline(filepath: str) -> dict:
    """
    Run the complete PMX export pipeline.

    Stages:
    1. Mesh validation + auto-repair
    2. Skeleton verification
    3. Weight paint verification
    4. Physics verification
    5. Morph verification
    6. PMX file export via mmd_tools

    Returns: {"success": bool, "stages": list[dict], "error": str}
    """
    import bpy

    body = find_aimm_object("body")
    skeleton = find_aimm_object("skeleton")

    if body is None:
        return {"success": False, "error": "未找到角色模型，请先创建角色", "stages": []}

    stages = []

    # Stage 1: Mesh validation
    from .mesh_validation import validate_and_repair
    result = validate_and_repair(body)
    stages.append({"name": "网格验证", "result": result})
    if not result["success"]:
        return {"success": False, "error": "网格验证失败", "stages": stages}

    # Stage 2: Skeleton verification
    if skeleton:
        from .skeleton_setup import verify_skeleton, rename_bones_for_pmx
        skel_result = verify_skeleton(skeleton)
        stages.append({"name": "骨骼验证", "result": skel_result})

        if skel_result["missing_bones"]:
            stages[-1]["result"]["warning"] = f"缺少骨骼: {', '.join(skel_result['missing_bones'])}"

        rename_result = rename_bones_for_pmx(skeleton)
        stages.append({"name": "骨骼命名", "result": rename_result})
    else:
        stages.append({"name": "骨骼验证", "result": {"success": False, "warning": "未配置骨骼，建议先运行 setup_skeleton"}})

    # Stage 3: Weight verification
    if skeleton:
        from .weight_paint import verify_weights, fix_unweighted_vertices
        weight_result = verify_weights(body, skeleton)
        stages.append({"name": "权重检查", "result": weight_result})

        if not weight_result["success"] and weight_result["unweighted_count"] > 0:
            fix_result = fix_unweighted_vertices(body, skeleton)
            stages.append({"name": "权重修复", "result": fix_result})
    else:
        stages.append({"name": "权重检查", "result": {"success": False, "warning": "无骨骼，跳过权重检查"}})

    # Stage 4: Physics verification
    from .physics_setup import verify_physics
    physics_result = verify_physics()
    stages.append({"name": "物理验证", "result": physics_result})

    # Stage 5: Morph verification
    from .morph_setup import verify_morphs
    morph_result = verify_morphs(body)
    stages.append({"name": "表情验证", "result": morph_result})

    # Stage 6: PMX Export
    from .mmd_tools_compat import is_mmd_tools_available, export_pmx_file, get_install_guidance

    if not is_mmd_tools_available():
        # Fallback: save as .blend file instead
        blend_path = filepath.replace('.pmx', '.blend')
        bpy.ops.wm.save_as_mainfile(filepath=blend_path)
        stages.append({
            "name": "PMX导出",
            "result": {
                "success": False,
                "error": "mmd_tools 未安装，无法直接导出 PMX",
                "fallback": f"已保存为 Blender 文件: {blend_path}",
                "guidance": get_install_guidance(),
            }
        })
        return {
            "success": False,
            "error": "mmd_tools 未安装，已保存为 .blend 文件",
            "stages": stages,
            "fallback_path": blend_path,
        }

    # Export via mmd_tools
    export_result = export_pmx_file(filepath, skeleton)
    stages.append({"name": "PMX导出", "result": export_result})

    # Collect all warnings
    all_warnings = []
    for stage in stages:
        if "warnings" in stage.get("result", {}):
            all_warnings.extend(stage["result"]["warnings"])

    return {
        "success": export_result.get("success", False),
        "filepath": filepath,
        "stages": stages,
        "warnings": all_warnings,
    }


def get_pipeline_status() -> dict:
    """
    Quick check of all pipeline stages without running them.
    Useful for the validate_pmx command.
    """
    body = find_aimm_object("body")
    skeleton = find_aimm_object("skeleton")

    status = {
        "body_exists": body is not None,
        "skeleton_exists": skeleton is not None,
        "has_shape_keys": body is not None and body.data.shape_keys is not None if body and body.type == 'MESH' else False,
    }

    from .mmd_tools_compat import is_mmd_tools_available
    status["mmd_tools_available"] = is_mmd_tools_available()

    return status
