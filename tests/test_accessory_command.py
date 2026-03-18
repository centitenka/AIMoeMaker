from commands.accessory import AddAccessory, RemoveAccessory
from core.model_state import ModelState, AccessoryItem

def test_add_accessory():
    state = ModelState()
    cmd = AddAccessory()
    result = cmd.execute({"type": "cat_ears", "position": [0, 0, 1.6]}, {"model_state": state, "bpy_available": False})
    assert result["success"] is True
    assert len(state.accessories) == 1
    assert state.accessories[0].accessory_type == "cat_ears"

def test_remove_accessory():
    state = ModelState()
    state.accessories.append(AccessoryItem(accessory_type="ribbon"))
    state.accessories.append(AccessoryItem(accessory_type="glasses"))
    cmd = RemoveAccessory()
    result = cmd.execute({"index": 0}, {"model_state": state, "bpy_available": False})
    assert result["success"] is True
    assert len(state.accessories) == 1
    assert state.accessories[0].accessory_type == "glasses"

def test_remove_accessory_by_type():
    state = ModelState()
    state.accessories.append(AccessoryItem(accessory_type="ribbon"))
    cmd = RemoveAccessory()
    result = cmd.execute({"type": "ribbon"}, {"model_state": state, "bpy_available": False})
    assert result["success"] is True
    assert len(state.accessories) == 0

def test_remove_accessory_not_found():
    state = ModelState()
    cmd = RemoveAccessory()
    result = cmd.execute({"type": "nonexistent"}, {"model_state": state, "bpy_available": False})
    assert result["success"] is False
