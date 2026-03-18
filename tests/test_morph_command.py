from commands.morph import CreateMorph, AddExpressionSet
from core.model_state import ModelState

def test_create_morph():
    state = ModelState()
    cmd = CreateMorph()
    result = cmd.execute({"name": "smile", "category": "mouth"}, {"model_state": state, "bpy_available": False})
    assert result["success"] is True
    assert "smile" in state.morphs.expressions

def test_add_expression_set():
    state = ModelState()
    cmd = AddExpressionSet()
    result = cmd.execute({"preset": "standard"}, {"model_state": state, "bpy_available": False})
    assert result["success"] is True
    assert len(state.morphs.expressions) > 0
    assert "まばたき" in state.morphs.expressions

def test_add_expression_set_no_duplicates():
    state = ModelState()
    cmd = AddExpressionSet()
    cmd.execute({"preset": "standard"}, {"model_state": state, "bpy_available": False})
    count = len(state.morphs.expressions)
    cmd.execute({"preset": "standard"}, {"model_state": state, "bpy_available": False})
    assert len(state.morphs.expressions) == count
