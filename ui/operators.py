import bpy
import threading
import queue
from ai.provider import AIProviderConfig
from ai.adapters.openai_compat import OpenAICompatAdapter
from core.session import SessionManager
from core.intent_router import IntentRouter
from core.command_engine import CommandEngine
from commands.body import BODY_COMMANDS
from prompts.system_prompt import build_system_prompt
from utils.undo import push_undo, undo

_session = None
_engine = None
_response_queue = queue.Queue()

def get_session():
    global _session
    if _session is None:
        _session = SessionManager()
    return _session

def get_engine():
    global _engine
    if _engine is None:
        _engine = CommandEngine()
        for cmd_cls in BODY_COMMANDS:
            _engine.register(cmd_cls)
    return _engine

def _get_addon_name():
    pkg = __package__
    if pkg and '.' in pkg:
        return pkg.rsplit('.', 1)[0]
    return pkg or "AIMoeMaker"

def _get_adapter(context):
    prefs = context.preferences.addons[_get_addon_name()].preferences
    config = AIProviderConfig(
        api_key=prefs.api_key, endpoint=prefs.api_endpoint,
        model=prefs.model_name, max_tokens=prefs.max_tokens,
        temperature=prefs.temperature,
    )
    return OpenAICompatAdapter(config)


class AIMM_OT_SendMessage(bpy.types.Operator):
    bl_idname = "aimm.send_message"
    bl_label = "发送消息"
    bl_description = "发送消息给 AI 助手"

    def execute(self, context):
        scene = context.scene
        user_input = scene.aimm_chat_input.strip()
        if not user_input:
            return {'CANCELLED'}
        session = get_session()
        session.add_message("user", user_input)
        scene.aimm_chat_input = ""
        scene.aimm_is_loading = True

        adapter = _get_adapter(context)
        system_prompt = build_system_prompt(session.model_state.to_summary())
        context_messages = session.get_context_messages(max_turns=10)

        thread = threading.Thread(
            target=self._ai_call, args=(adapter, system_prompt, context_messages), daemon=True)
        thread.start()
        bpy.app.timers.register(self._check_completion, first_interval=0.5)
        return {'FINISHED'}

    @staticmethod
    def _ai_call(adapter, system_prompt, context_messages):
        ai_response = adapter.chat(messages=context_messages, system_prompt=system_prompt)
        _response_queue.put({
            "reply": ai_response.reply,
            "intents": [{"type": i.intent_type, "action": i.action, "params": i.params, "code": i.code, "description": i.description} for i in ai_response.intents],
        })

    @staticmethod
    def _check_completion():
        try:
            pending = _response_queue.get_nowait()
        except queue.Empty:
            return 0.5

        session = get_session()
        engine = get_engine()
        reply = pending["reply"]

        from prompts.intent_schema import Intent, AIResponse
        intents = [Intent(intent_type=i["type"], action=i["action"], params=i["params"], code=i["code"], description=i["description"]) for i in pending["intents"]]
        response = AIResponse(reply=reply, intents=intents)

        if response.intents:
            push_undo("AI操作")
            router = IntentRouter(
                command_handler=lambda action, params: engine.execute(action, params, context={"model_state": session.model_state, "bpy_available": True})
            )
            results = router.execute(response)
            if any(not r.get("success", False) for r in results):
                undo()
            session.add_message("assistant", reply, intents_executed=results)
        else:
            session.add_message("assistant", reply)

        bpy.context.scene.aimm_is_loading = False
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()
        return None


class AIMM_OT_Undo(bpy.types.Operator):
    bl_idname = "aimm.undo"
    bl_label = "撤销"
    def execute(self, context):
        undo()
        return {'FINISHED'}


class AIMM_OT_ClearChat(bpy.types.Operator):
    bl_idname = "aimm.clear_chat"
    bl_label = "清空对话"
    def execute(self, context):
        get_session().clear()
        return {'FINISHED'}


OPERATOR_CLASSES = [AIMM_OT_SendMessage, AIMM_OT_Undo, AIMM_OT_ClearChat]
