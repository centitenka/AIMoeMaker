from commands.body import CreateBaseBody, AdjustProportions, SetHeight
from core.model_state import ModelState


def test_create_base_body_updates_state():
    state = ModelState()
    cmd = CreateBaseBody()
    context = {"model_state": state, "bpy_available": False}
    result = cmd.execute({"body_type": "loli", "height": 145.0}, context)
    assert result["success"] is True
    assert state.body.body_type == "loli"
    assert state.body.height == 145.0


def test_create_base_body_defaults():
    state = ModelState()
    cmd = CreateBaseBody()
    context = {"model_state": state, "bpy_available": False}
    result = cmd.execute({}, context)
    assert result["success"] is True
    assert state.body.body_type == "default"
    assert state.body.height == 158.0


def test_set_height():
    state = ModelState()
    cmd = SetHeight()
    context = {"model_state": state, "bpy_available": False}
    result = cmd.execute({"height": 170.0}, context)
    assert result["success"] is True
    assert state.body.height == 170.0


def test_set_height_validation():
    state = ModelState()
    cmd = SetHeight()
    context = {"model_state": state, "bpy_available": False}
    result = cmd.execute({"height": -10.0}, context)
    assert result["success"] is False
    assert "范围" in result["error"]


def test_adjust_proportions():
    state = ModelState()
    cmd = AdjustProportions()
    context = {"model_state": state, "bpy_available": False}
    result = cmd.execute({"bust": 0.7, "waist": 0.3}, context)
    assert result["success"] is True
    assert state.body.bust == 0.7
    assert state.body.waist == 0.3
    assert state.body.hip == 0.5  # unchanged
