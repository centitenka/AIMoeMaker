from commands.base import BaseCommand
from core.model_state import ModelState

STANDARD_EXPRESSIONS = ["真面目", "困る", "にこり", "怒り", "上", "下", "まばたき", "笑い", "ウィンク", "ウィンク右", "ウィンク２", "あ", "い", "う", "え", "お", "△", "∧", "ω", "照れ"]

class CreateMorph(BaseCommand):
    action = "create_morph"
    def execute(self, params, context):
        state: ModelState = context["model_state"]
        name = params.get("name", "")
        if not name:
            return {"success": False, "error": "请指定表情名称(name)"}
        if not hasattr(state.morphs, "expressions"):
            state.morphs.expressions = []
        if name not in state.morphs.expressions:
            state.morphs.expressions.append(name)
        return {"success": True, "message": f"已创建表情: {name}"}

class AddExpressionSet(BaseCommand):
    action = "add_expression_set"
    def execute(self, params, context):
        state: ModelState = context["model_state"]
        preset = params.get("preset", "standard")
        if preset != "standard":
            return {"success": False, "error": f"未知表情预设: {preset}，可选: standard"}
        if not hasattr(state.morphs, "expressions"):
            state.morphs.expressions = []
        for expr in STANDARD_EXPRESSIONS:
            if expr not in state.morphs.expressions:
                state.morphs.expressions.append(expr)
        return {"success": True, "message": f"已添加{preset}表情集（{len(STANDARD_EXPRESSIONS)}个表情）"}

MORPH_COMMANDS = [CreateMorph, AddExpressionSet]
