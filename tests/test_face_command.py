from commands.face import SetEyeShape, SetEyeColor, AdjustFaceShape
from core.model_state import ModelState, FaceState

def test_set_eye_shape():
    state = ModelState()
    state.face = FaceState()
    cmd = SetEyeShape()
    result = cmd.execute({"shape": "cat"}, {"model_state": state, "bpy_available": False})
    assert result["success"] is True
    assert state.face.eye_shape == "cat"

def test_set_eye_shape_creates_face():
    state = ModelState()
    cmd = SetEyeShape()
    result = cmd.execute({"shape": "round"}, {"model_state": state, "bpy_available": False})
    assert result["success"] is True
    assert state.face is not None
    assert state.face.eye_shape == "round"

def test_set_eye_color():
    state = ModelState()
    state.face = FaceState()
    cmd = SetEyeColor()
    result = cmd.execute({"color": "#FF0000"}, {"model_state": state, "bpy_available": False})
    assert result["success"] is True
    assert state.face.eye_color == "#FF0000"

def test_adjust_face_shape():
    state = ModelState()
    state.face = FaceState()
    cmd = AdjustFaceShape()
    result = cmd.execute({"shape": "heart"}, {"model_state": state, "bpy_available": False})
    assert result["success"] is True
    assert state.face.face_shape == "heart"
