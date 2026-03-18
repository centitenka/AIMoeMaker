from commands.physics import SetupHairPhysics, SetupClothPhysics
from core.model_state import ModelState, HairState, ClothingItem

def test_setup_hair_physics():
    state = ModelState()
    state.hair = HairState()
    cmd = SetupHairPhysics()
    result = cmd.execute({"stiffness": 0.5, "damping": 0.3}, {"model_state": state, "bpy_available": False})
    assert result["success"] is True
    assert state.physics.rigid_body_count > 0

def test_setup_hair_physics_no_hair():
    state = ModelState()
    cmd = SetupHairPhysics()
    result = cmd.execute({}, {"model_state": state, "bpy_available": False})
    assert result["success"] is False

def test_setup_cloth_physics():
    state = ModelState()
    state.clothing.append(ClothingItem(clothing_type="skirt"))
    cmd = SetupClothPhysics()
    result = cmd.execute({"index": 0}, {"model_state": state, "bpy_available": False})
    assert result["success"] is True
    assert state.clothing[0].physics_enabled is True
