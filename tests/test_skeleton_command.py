from commands.skeleton import SetupSkeleton, AutoWeightPaint
from core.model_state import ModelState

def test_setup_skeleton():
    state = ModelState()
    cmd = SetupSkeleton()
    result = cmd.execute({}, {"model_state": state, "bpy_available": False})
    assert result["success"] is True
    assert state.skeleton.is_configured is True
    assert state.skeleton.ik_setup is True

def test_auto_weight_paint():
    state = ModelState()
    state.skeleton.is_configured = True
    cmd = AutoWeightPaint()
    result = cmd.execute({}, {"model_state": state, "bpy_available": False})
    assert result["success"] is True

def test_auto_weight_paint_no_skeleton():
    state = ModelState()
    cmd = AutoWeightPaint()
    result = cmd.execute({}, {"model_state": state, "bpy_available": False})
    assert result["success"] is False
