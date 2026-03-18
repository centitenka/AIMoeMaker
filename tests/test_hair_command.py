from commands.hair import AddHair, ModifyHairStyle, SetHairColor
from core.model_state import ModelState, HairState

def test_add_hair():
    state = ModelState()
    cmd = AddHair()
    result = cmd.execute({"style": "twintail", "colors": ["#FFB6C1", "#FF69B4"], "length": 0.8}, {"model_state": state, "bpy_available": False})
    assert result["success"] is True
    assert state.hair is not None
    assert state.hair.style == "twintail"
    assert state.hair.colors == ["#FFB6C1", "#FF69B4"]
    assert state.hair.length == 0.8

def test_add_hair_defaults():
    state = ModelState()
    cmd = AddHair()
    result = cmd.execute({}, {"model_state": state, "bpy_available": False})
    assert result["success"] is True
    assert state.hair.style == "short"
    assert state.hair.colors == ["#000000"]

def test_modify_hair_style():
    state = ModelState()
    state.hair = HairState(style="short")
    cmd = ModifyHairStyle()
    result = cmd.execute({"style": "ponytail"}, {"model_state": state, "bpy_available": False})
    assert result["success"] is True
    assert state.hair.style == "ponytail"

def test_modify_hair_no_hair():
    state = ModelState()
    cmd = ModifyHairStyle()
    result = cmd.execute({"style": "ponytail"}, {"model_state": state, "bpy_available": False})
    assert result["success"] is False

def test_set_hair_color():
    state = ModelState()
    state.hair = HairState()
    cmd = SetHairColor()
    result = cmd.execute({"colors": ["#FF0000"], "gradient": True}, {"model_state": state, "bpy_available": False})
    assert result["success"] is True
    assert state.hair.colors == ["#FF0000"]
    assert state.hair.gradient is True
