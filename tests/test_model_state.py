import json
from core.model_state import ModelState


def test_default_model_state():
    state = ModelState()
    assert state.body.height == 158.0
    assert state.body.body_type == "default"
    assert state.hair is None
    assert state.clothing == []


def test_model_state_to_dict():
    state = ModelState()
    d = state.to_dict()
    assert d["schema_version"] == 1
    assert d["body"]["height"] == 158.0


def test_model_state_from_dict():
    state = ModelState()
    state.body.height = 165.0
    d = state.to_dict()
    restored = ModelState.from_dict(d)
    assert restored.body.height == 165.0


def test_model_state_summary():
    state = ModelState()
    summary = state.to_summary()
    assert isinstance(summary, str)
    assert "身体" in summary


def test_model_state_to_json_roundtrip():
    state = ModelState()
    state.body.height = 145.0
    state.body.body_type = "loli"
    json_str = json.dumps(state.to_dict(), ensure_ascii=False)
    restored = ModelState.from_dict(json.loads(json_str))
    assert restored.body.height == 145.0
    assert restored.body.body_type == "loli"
