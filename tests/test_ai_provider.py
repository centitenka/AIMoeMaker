import json
from unittest.mock import patch, MagicMock
from ai.provider import AIProviderConfig
from ai.adapters.openai_compat import OpenAICompatAdapter


def _mock_urlopen(response_body: dict):
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(response_body).encode('utf-8')
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)
    return mock_response


def test_openai_compat_chat():
    config = AIProviderConfig(api_key="test-key", endpoint="https://api.example.com/v1/chat/completions", model="gpt-4")
    adapter = OpenAICompatAdapter(config)
    mock_ai_reply = {"reply": "好的，我来创建一个萝莉体型。", "intents": [{"type": "command", "action": "create_base_body", "params": {"body_type": "loli"}}]}
    mock_response = _mock_urlopen({"choices": [{"message": {"content": json.dumps(mock_ai_reply, ensure_ascii=False)}}]})
    with patch("urllib.request.urlopen", return_value=mock_response):
        result = adapter.chat(messages=[{"role": "user", "content": "创建一个萝莉角色"}], system_prompt="你是建模助手")
    assert result.reply == "好的，我来创建一个萝莉体型。"
    assert len(result.intents) == 1
    assert result.intents[0].action == "create_base_body"


def test_openai_compat_network_error():
    config = AIProviderConfig(api_key="test-key", endpoint="https://api.example.com/v1/chat/completions", model="gpt-4")
    adapter = OpenAICompatAdapter(config)
    with patch("urllib.request.urlopen", side_effect=Exception("Connection refused")):
        result = adapter.chat(messages=[{"role": "user", "content": "hello"}], system_prompt="test")
    assert len(result.intents) == 0


def test_openai_compat_malformed_response():
    config = AIProviderConfig(api_key="test-key", endpoint="https://api.example.com/v1/chat/completions", model="gpt-4")
    adapter = OpenAICompatAdapter(config)
    mock_response = _mock_urlopen({"choices": [{"message": {"content": "我不太理解你的意思"}}]})
    with patch("urllib.request.urlopen", return_value=mock_response):
        result = adapter.chat(messages=[{"role": "user", "content": "blah"}], system_prompt="test")
    assert "理解" in result.reply
    assert len(result.intents) == 0
