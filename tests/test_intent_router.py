from core.intent_router import IntentRouter
from prompts.intent_schema import Intent, AIResponse


def test_router_dispatches_command():
    results = []
    def mock_command_handler(action, params):
        results.append(("command", action, params))
        return {"success": True}
    router = IntentRouter(command_handler=mock_command_handler)
    intent = Intent(intent_type="command", action="create_base_body",
                    params={"body_type": "loli", "height": 145.0})
    response = AIResponse(reply="OK", intents=[intent])
    execution_results = router.execute(response)
    assert len(results) == 1
    assert results[0] == ("command", "create_base_body", {"body_type": "loli", "height": 145.0})
    assert execution_results[0]["success"] is True


def test_router_handles_empty_intents():
    router = IntentRouter(command_handler=lambda a, p: None)
    response = AIResponse(reply="有什么可以帮你的？", intents=[])
    execution_results = router.execute(response)
    assert execution_results == []


def test_router_stops_on_failure():
    call_count = 0
    def failing_handler(action, params):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RuntimeError("模拟失败")
        return {"success": True}
    router = IntentRouter(command_handler=failing_handler)
    intents = [
        Intent(intent_type="command", action="set_height", params={"height": 160}),
        Intent(intent_type="command", action="set_height", params={"height": 170}),
    ]
    response = AIResponse(reply="OK", intents=intents)
    execution_results = router.execute(response)
    assert call_count == 1
    assert execution_results[0]["success"] is False
    assert "模拟失败" in execution_results[0]["error"]


def test_router_unknown_type_skipped():
    router = IntentRouter(command_handler=lambda a, p: {"success": True})
    intent = Intent(intent_type="unknown_type", action="foo")
    response = AIResponse(reply="OK", intents=[intent])
    execution_results = router.execute(response)
    assert len(execution_results) == 1
    assert execution_results[0]["success"] is False
    assert "未知" in execution_results[0]["error"]
