from typing import Type
from ..commands.base import BaseCommand
from .step_validator import run_step_validation


class CommandEngine:
    def __init__(self):
        self._commands: dict[str, BaseCommand] = {}

    def register(self, command_cls: Type[BaseCommand]):
        instance = command_cls()
        self._commands[instance.action] = instance

    def execute(self, action: str, params: dict, context: dict) -> dict:
        command = self._commands.get(action)
        if command is None:
            return {"success": False, "error": f"未知指令: {action}"}
        try:
            result = command.execute(params, context)
        except Exception as e:
            return {"success": False, "error": str(e)}

        # Run post-step validation on successful commands
        if result.get("success", False):
            vr = run_step_validation(action, params, result, context)
            if vr.issues:
                result["validation"] = vr.to_dict()

        return result

    def list_actions(self) -> list[str]:
        return list(self._commands.keys())
