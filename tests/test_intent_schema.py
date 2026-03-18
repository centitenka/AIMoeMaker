from prompts.intent_schema import parse_ai_response, _extract_json


def test_parse_valid_json():
    raw = '{"reply": "你好", "intents": [{"type": "command", "action": "set_height", "params": {"height": 160}}]}'
    result = parse_ai_response(raw)
    assert result.reply == "你好"
    assert len(result.intents) == 1
    assert result.intents[0].action == "set_height"


def test_parse_json_in_code_fence():
    raw = '```json\n{"reply": "OK", "intents": []}\n```'
    result = parse_ai_response(raw)
    assert result.reply == "OK"
    assert result.intents == []


def test_parse_non_json_fallback():
    raw = "我不太理解你的意思"
    result = parse_ai_response(raw)
    assert result.reply == raw
    assert result.intents == []


def test_parse_json_with_surrounding_text():
    raw = '好的，这是我的回复：\n{"reply": "创建中", "intents": [{"type": "command", "action": "create_base_body", "params": {}}]}\n以上。'
    result = parse_ai_response(raw)
    assert result.reply == "创建中"
    assert len(result.intents) == 1


def test_parse_json_with_braces_in_strings():
    raw = '{"reply": "使用 { 和 } 要小心", "intents": []}'
    result = parse_ai_response(raw)
    assert result.reply == "使用 { 和 } 要小心"


def test_extract_json_returns_none_for_no_json():
    assert _extract_json("hello world") is None
