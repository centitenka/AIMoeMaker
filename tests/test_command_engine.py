import pytest
from core.command_engine import CommandEngine
from commands.base import BaseCommand


class DummyCommand(BaseCommand):
    action = "test_action"
    calls = []
    def execute(self, params: dict, context: dict) -> dict:
        DummyCommand.calls.append(params)
        return {"success": True, "message": "测试指令已执行"}


def test_register_and_execute():
    DummyCommand.calls = []
    engine = CommandEngine()
    engine.register(DummyCommand)
    result = engine.execute("test_action", {"value": 42}, context={})
    assert result["success"] is True
    assert DummyCommand.calls == [{"value": 42}]


def test_unknown_action_fails():
    engine = CommandEngine()
    result = engine.execute("nonexistent", {}, context={})
    assert result["success"] is False
    assert "未知" in result["error"]


def test_command_exception_caught():
    class FailingCommand(BaseCommand):
        action = "fail_action"
        def execute(self, params, context):
            raise ValueError("something broke")
    engine = CommandEngine()
    engine.register(FailingCommand)
    result = engine.execute("fail_action", {}, context={})
    assert result["success"] is False
    assert "something broke" in result["error"]
