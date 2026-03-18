from commands.export import ValidatePmx, ExportPmx
from core.model_state import ModelState

def test_validate_pmx_incomplete():
    state = ModelState()
    cmd = ValidatePmx()
    result = cmd.execute({}, {"model_state": state, "bpy_available": False})
    assert result["success"] is True
    assert len(result.get("warnings", [])) > 0

def test_validate_pmx_complete():
    state = ModelState()
    state.skeleton.is_configured = True
    state.skeleton.ik_setup = True
    state.morphs.expressions = ["まばたき", "あ"]
    from core.model_state import HairState, ClothingItem
    state.hair = HairState()
    state.clothing.append(ClothingItem(clothing_type="dress"))
    cmd = ValidatePmx()
    result = cmd.execute({}, {"model_state": state, "bpy_available": False})
    assert result["success"] is True
    # In test env, mmd_tools isn't installed so there may be that warning
    non_mmd_warnings = [w for w in result.get("warnings", []) if "mmd_tools" not in w]
    assert len(non_mmd_warnings) == 0

def test_export_pmx_no_bpy():
    state = ModelState()
    cmd = ExportPmx()
    result = cmd.execute({"path": "/tmp/test.pmx"}, {"model_state": state, "bpy_available": False})
    assert result["success"] is False
    assert "Blender" in result["error"]
