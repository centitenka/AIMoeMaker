"""End-to-end integration test: user message → AI response → intent → command → state update."""
import json
from unittest.mock import patch, MagicMock
from core.session import SessionManager
from core.intent_router import IntentRouter
from core.command_engine import CommandEngine
from commands.body import BODY_COMMANDS
from ai.adapters.openai_compat import OpenAICompatAdapter
from ai.provider import AIProviderConfig
from prompts.system_prompt import build_system_prompt


def _mock_ai_response(reply, intents):
    ai_reply = {"reply": reply, "intents": intents}
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps({"choices": [{"message": {"content": json.dumps(ai_reply, ensure_ascii=False)}}]}).encode("utf-8")
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


def test_full_flow_create_body():
    session = SessionManager()
    engine = CommandEngine()
    for cmd_cls in BODY_COMMANDS:
        engine.register(cmd_cls)
    session.add_message("user", "创建一个萝莉角色，身高145cm")
    mock_response = _mock_ai_response("好的，我来创建一个145cm的萝莉体型角色。", [{"type": "command", "action": "create_base_body", "params": {"body_type": "loli", "height": 145.0}}])
    config = AIProviderConfig(api_key="test", endpoint="https://test.com/v1/chat/completions", model="test")
    adapter = OpenAICompatAdapter(config)
    with patch("urllib.request.urlopen", return_value=mock_response):
        system_prompt = build_system_prompt(session.model_state.to_summary())
        ai_response = adapter.chat(messages=session.get_context_messages(), system_prompt=system_prompt)
    router = IntentRouter(command_handler=lambda action, params: engine.execute(action, params, context={"model_state": session.model_state, "bpy_available": False}))
    results = router.execute(ai_response)
    assert results[0]["success"] is True
    assert session.model_state.body.body_type == "loli"
    assert session.model_state.body.height == 145.0
    session.add_message("assistant", ai_response.reply, intents_executed=results)
    assert len(session.conversation) == 2


def test_full_flow_multi_intent():
    session = SessionManager()
    engine = CommandEngine()
    for cmd_cls in BODY_COMMANDS:
        engine.register(cmd_cls)
    mock_response = _mock_ai_response("好的，我来创建角色并调整比例。", [
        {"type": "command", "action": "create_base_body", "params": {"body_type": "adult", "height": 170.0}},
        {"type": "command", "action": "adjust_proportions", "params": {"bust": 0.7, "waist": 0.4}},
    ])
    config = AIProviderConfig(api_key="test", endpoint="https://test.com/v1/chat/completions", model="test")
    adapter = OpenAICompatAdapter(config)
    with patch("urllib.request.urlopen", return_value=mock_response):
        ai_response = adapter.chat(messages=[], system_prompt="test")
    router = IntentRouter(command_handler=lambda action, params: engine.execute(action, params, context={"model_state": session.model_state, "bpy_available": False}))
    results = router.execute(ai_response)
    assert len(results) == 2
    assert all(r["success"] for r in results)
    assert session.model_state.body.height == 170.0
    assert session.model_state.body.bust == 0.7


def test_full_flow_ai_asks_question():
    mock_response = _mock_ai_response("你想要什么风格的角色呢？比如萝莉、少女、还是成人体型？", [])
    config = AIProviderConfig(api_key="test", endpoint="https://test.com/v1/chat/completions", model="test")
    adapter = OpenAICompatAdapter(config)
    with patch("urllib.request.urlopen", return_value=mock_response):
        ai_response = adapter.chat(messages=[], system_prompt="test")
    router = IntentRouter(command_handler=lambda action, params: {"success": True})
    results = router.execute(ai_response)
    assert results == []
    assert "风格" in ai_response.reply
