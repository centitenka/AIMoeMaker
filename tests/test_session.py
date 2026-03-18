import json
import tempfile
import os
from core.session import SessionManager
from core.model_state import ModelState


def test_add_message():
    session = SessionManager()
    session.add_message("user", "创建一个萝莉角色")
    session.add_message("assistant", "好的，我来创建。")
    assert len(session.conversation) == 2
    assert session.conversation[0]["role"] == "user"
    assert session.conversation[1]["role"] == "assistant"


def test_get_context_messages():
    session = SessionManager()
    for i in range(30):
        session.add_message("user", f"消息{i}")
        session.add_message("assistant", f"回复{i}")
    messages = session.get_context_messages(max_turns=5)
    assert len(messages) == 10  # 5 turns = 10 messages


def test_mark_key_decision():
    session = SessionManager()
    session.add_message("user", "我要一个银发红瞳的角色")
    session.mark_key_decision(0)
    messages = session.get_context_messages(max_turns=2)
    assert any("银发红瞳" in m["content"] for m in messages)


def test_save_and_load_project():
    with tempfile.TemporaryDirectory() as tmpdir:
        session = SessionManager()
        session.add_message("user", "你好")
        session.model_state.body.height = 145.0
        session.save_project(tmpdir, "test_project")
        session2 = SessionManager()
        session2.load_project(tmpdir, "test_project")
        assert len(session2.conversation) == 1
        assert session2.model_state.body.height == 145.0


def test_model_state_summary_in_context():
    session = SessionManager()
    session.model_state.body.height = 145.0
    session.model_state.body.body_type = "loli"
    summary = session.model_state.to_summary()
    assert "145" in summary
    assert "loli" in summary
