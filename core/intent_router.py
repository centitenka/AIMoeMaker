from typing import Callable, Optional
from prompts.intent_schema import AIResponse, Intent


class IntentRouter:
    def __init__(self, command_handler=None, code_handler=None, asset_handler=None):
        self._command_handler = command_handler
        self._code_handler = code_handler
        self._asset_handler = asset_handler

    def execute(self, response: AIResponse) -> list[dict]:
        results = []
        for intent in response.intents:
            result = self._execute_one(intent)
            results.append(result)
            if not result.get("success", False):
                break
        return results

    def _execute_one(self, intent: Intent) -> dict:
        try:
            if intent.intent_type == "command":
                if self._command_handler is None:
                    return {"success": False, "error": "指令处理器未注册"}
                result = self._command_handler(intent.action, intent.params)
                return result if result else {"success": True}
            elif intent.intent_type == "code":
                if self._code_handler is None:
                    return {"success": False, "error": "代码沙箱未注册"}
                result = self._code_handler(intent.code, intent.description)
                return result if result else {"success": True}
            elif intent.intent_type == "asset":
                if self._asset_handler is None:
                    return {"success": False, "error": "资产管理器未注册"}
                result = self._asset_handler(intent.action, intent.params)
                return result if result else {"success": True}
            else:
                return {"success": False, "error": f"未知的意图类型: {intent.intent_type}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
