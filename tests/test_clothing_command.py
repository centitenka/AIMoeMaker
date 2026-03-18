from commands.clothing import AddClothing, ModifyClothing, SetFabricMaterial
from core.model_state import ModelState, ClothingItem

def test_add_clothing():
    state = ModelState()
    cmd = AddClothing()
    result = cmd.execute({"type": "gothic_dress", "color": "#000000"}, {"model_state": state, "bpy_available": False})
    assert result["success"] is True
    assert len(state.clothing) == 1
    assert state.clothing[0].clothing_type == "gothic_dress"

def test_add_multiple_clothing():
    state = ModelState()
    cmd = AddClothing()
    cmd.execute({"type": "shirt"}, {"model_state": state, "bpy_available": False})
    cmd.execute({"type": "skirt"}, {"model_state": state, "bpy_available": False})
    assert len(state.clothing) == 2

def test_modify_clothing():
    state = ModelState()
    state.clothing.append(ClothingItem(clothing_type="dress", color="#FFFFFF"))
    cmd = ModifyClothing()
    result = cmd.execute({"index": 0, "color": "#000000"}, {"model_state": state, "bpy_available": False})
    assert result["success"] is True
    assert state.clothing[0].color == "#000000"

def test_modify_clothing_invalid_index():
    state = ModelState()
    cmd = ModifyClothing()
    result = cmd.execute({"index": 0, "color": "#000000"}, {"model_state": state, "bpy_available": False})
    assert result["success"] is False

def test_set_fabric_material():
    state = ModelState()
    state.clothing.append(ClothingItem(clothing_type="dress"))
    cmd = SetFabricMaterial()
    result = cmd.execute({"index": 0, "material": "silk", "physics_enabled": True}, {"model_state": state, "bpy_available": False})
    assert result["success"] is True
    assert state.clothing[0].material == "silk"
    assert state.clothing[0].physics_enabled is True
