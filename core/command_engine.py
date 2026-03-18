from typing import Type
from commands.base import BaseCommand


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
            return command.execute(params, context)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_actions(self) -> list[str]:
        return list(self._commands.keys())
