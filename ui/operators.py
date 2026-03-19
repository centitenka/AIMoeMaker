import bpy
import threading
import queue
from ..ai.provider import AIProviderConfig
from ..ai.adapters.openai_compat import OpenAICompatAdapter
from ..core.session import SessionManager
from ..core.intent_router import IntentRouter
from ..core.command_engine import CommandEngine
from ..asset_mgr.manager import AssetManager
from ..commands.body import BODY_COMMANDS
from ..commands.hair import HAIR_COMMANDS
from ..commands.face import FACE_COMMANDS
from ..commands.clothing import CLOTHING_COMMANDS
from ..commands.accessory import ACCESSORY_COMMANDS
from ..commands.skeleton import SKELETON_COMMANDS
from ..commands.physics import PHYSICS_COMMANDS
from ..commands.morph import MORPH_COMMANDS
from ..commands.export import EXPORT_COMMANDS
from ..commands.scene import SCENE_COMMANDS
from ..prompts.system_prompt import build_system_prompt
from ..core.code_sandbox import CodeSandbox
from ..utils.undo import push_undo, undo

def _snapshot_aimm_objects():
    """Return set of names of all objects tagged with aimm_type."""
    return {obj.name for obj in bpy.data.objects if obj.get("aimm_type")}

def _cleanup_new_aimm_objects(before_snapshot):
    """Delete any aimm-tagged objects that were created after the snapshot."""
    to_remove = []
    for obj in bpy.data.objects:
        if obj.get("aimm_type") and obj.name not in before_snapshot:
            to_remove.append(obj)
    # Unlink from collections first, then remove data
    for obj in to_remove:
        mesh_data = obj.data if obj.type == 'MESH' else None
        bpy.data.objects.remove(obj, do_unlink=True)
        # Clean up orphaned mesh data
        if mesh_data and mesh_data.users == 0:
            bpy.data.meshes.remove(mesh_data)

_session = None
_engine = None
_sandbox = None
_asset_manager = None
_response_queue = queue.Queue()

_VALIDATION_ICONS = {"error": "✗", "warning": "⚠", "info": "✓"}

# Auto-continue workflow state
_MAX_AUTO_CONTINUE = 10
_auto_continue_count = 0
_auto_continue_active = False
_stop_requested = False
_cached_adapter = None


def _tag_redraw_all():
    """Reliably tag all VIEW_3D UI regions for redraw.

    Uses window_managers iteration instead of bpy.context.screen,
    which is unreliable inside timer callbacks.
    """
    try:
        for wm in bpy.data.window_managers:
            for window in wm.windows:
                for area in window.screen.areas:
                    if area.type == 'VIEW_3D':
                        for region in area.regions:
                            if region.type == 'UI':
                                region.tag_redraw()
                        area.tag_redraw()
    except Exception:
        pass


def _collect_validation_notes(results: list[dict]) -> str:
    """Extract validation issues from command results into display text."""
    lines = []
    for r in results:
        validation = r.get("validation")
        if not validation or not validation.get("issues"):
            continue
        for issue in validation["issues"]:
            icon = _VALIDATION_ICONS.get(issue["level"], "•")
            lines.append(f"{icon} {issue['message']}")
    if not lines:
        return ""
    return "[验证] " + " | ".join(lines)

def _get_scene_overview() -> str:
    """Safely get scene overview for system prompt injection."""
    try:
        from ..blender_ops.scene_inspector import get_scene_overview
        return get_scene_overview()
    except Exception:
        return "（场景信息不可用）"


def get_session():
    global _session
    if _session is None:
        _session = SessionManager()
    return _session

def get_engine():
    global _engine
    if _engine is None:
        _engine = CommandEngine()
        all_commands = (
            BODY_COMMANDS + HAIR_COMMANDS + FACE_COMMANDS +
            CLOTHING_COMMANDS + ACCESSORY_COMMANDS + SKELETON_COMMANDS +
            PHYSICS_COMMANDS + MORPH_COMMANDS + EXPORT_COMMANDS +
            SCENE_COMMANDS
        )
        for cmd_cls in all_commands:
            _engine.register(cmd_cls)
    return _engine

def get_sandbox():
    global _sandbox
    if _sandbox is None:
        _sandbox = CodeSandbox(timeout=30)
    return _sandbox

def get_asset_manager():
    global _asset_manager
    if _asset_manager is None:
        import os
        # Store assets in Blender's user data path
        try:
            import bpy
            base = os.path.join(bpy.utils.resource_path('USER'), "AIMoeMaker", "asset_library")
        except Exception:
            base = os.path.join(os.path.expanduser("~"), ".aimoemaker", "asset_library")
        _asset_manager = AssetManager(base)
    return _asset_manager

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


def _build_result_summary(results: list[dict]) -> str:
    """Build a short summary of intent execution results for the AI context."""
    lines = []
    for r in results:
        action = r.get("action", "unknown")
        if r.get("success", False):
            lines.append(f"✓ {action} 成功")
        else:
            error = r.get("error", "未知错误")
            lines.append(f"✗ {action} 失败: {error}")
    return "\n".join(lines)


def _launch_ai_continuation():
    """Launch a new AI call for auto-continue workflow."""
    global _cached_adapter
    if _cached_adapter is None:
        return

    session = get_session()
    scene_overview = _get_scene_overview()
    system_prompt = build_system_prompt(session.model_state.to_summary(), scene_overview)
    context_messages = session.get_context_messages(max_turns=10)

    thread = threading.Thread(
        target=AIMM_OT_SendMessage._ai_call,
        args=(_cached_adapter, system_prompt, context_messages),
        daemon=True,
    )
    thread.start()


class AIMM_OT_SendMessage(bpy.types.Operator):
    bl_idname = "aimm.send_message"
    bl_label = "发送消息"
    bl_description = "发送消息给 AI 助手"

    def execute(self, context):
        global _auto_continue_count, _auto_continue_active, _stop_requested, _cached_adapter

        scene = context.scene
        user_input = scene.aimm_chat_input.strip()
        if not user_input:
            return {'CANCELLED'}
        session = get_session()
        session.add_message("user", user_input)
        scene.aimm_chat_input = ""
        scene.aimm_is_loading = True

        # Reset auto-continue state
        _auto_continue_count = 0
        _auto_continue_active = False
        _stop_requested = False

        adapter = _get_adapter(context)
        _cached_adapter = adapter
        scene_overview = _get_scene_overview()
        system_prompt = build_system_prompt(session.model_state.to_summary(), scene_overview)
        context_messages = session.get_context_messages(max_turns=10)

        thread = threading.Thread(
            target=self._ai_call, args=(adapter, system_prompt, context_messages), daemon=True)
        thread.start()
        bpy.app.timers.register(self._check_completion, first_interval=0.5)
        _tag_redraw_all()
        return {'FINISHED'}

    @staticmethod
    def _ai_call(adapter, system_prompt, context_messages):
        ai_response = adapter.chat(messages=context_messages, system_prompt=system_prompt)
        _response_queue.put({
            "reply": ai_response.reply,
            "intents": [{"type": i.intent_type, "action": i.action, "params": i.params, "code": i.code, "description": i.description} for i in ai_response.intents],
            "continue_workflow": ai_response.continue_workflow,
        })

    @staticmethod
    def _check_completion():
        global _auto_continue_count, _auto_continue_active, _stop_requested

        # Check stop request
        if _stop_requested:
            _auto_continue_active = False
            _stop_requested = False
            bpy.context.scene.aimm_is_loading = False
            _tag_redraw_all()
            return None

        try:
            pending = _response_queue.get_nowait()
        except queue.Empty:
            _tag_redraw_all()
            return 0.5

        session = get_session()
        engine = get_engine()
        reply = pending["reply"]
        continue_workflow = pending.get("continue_workflow", False)

        from ..prompts.intent_schema import Intent, AIResponse
        intents = [Intent(intent_type=i["type"], action=i["action"], params=i["params"], code=i["code"], description=i["description"]) for i in pending["intents"]]
        response = AIResponse(reply=reply, intents=intents, continue_workflow=continue_workflow)

        all_succeeded = True
        if response.intents:
            before = _snapshot_aimm_objects()
            sandbox = get_sandbox()
            asset_mgr = get_asset_manager()
            router = IntentRouter(
                command_handler=lambda action, params: engine.execute(action, params, context={"model_state": session.model_state, "bpy_available": True}),
                code_handler=lambda code, desc: sandbox.execute(code, desc),
                asset_handler=lambda action, params: asset_mgr.handle_intent(action, params),
            )
            results = router.execute(response)
            if any(not r.get("success", False) for r in results):
                _cleanup_new_aimm_objects(before)
                all_succeeded = False

            validation_notes = _collect_validation_notes(results)
            display_reply = reply
            if validation_notes:
                display_reply += "\n\n" + validation_notes
            session.add_message("assistant", display_reply, intents_executed=results)

            # Check if we should auto-continue
            if (continue_workflow and all_succeeded
                    and not _stop_requested
                    and _auto_continue_count < _MAX_AUTO_CONTINUE):
                _auto_continue_count += 1
                _auto_continue_active = True

                # Inject execution result summary so AI knows what happened
                result_summary = _build_result_summary(results)
                session.add_message("user", f"[系统] 上一步执行结果:\n{result_summary}\n请继续下一步。")

                # Launch next AI call
                _launch_ai_continuation()
                _tag_redraw_all()
                return 0.5  # Keep polling

            # Auto-continue limit reached
            if _auto_continue_count >= _MAX_AUTO_CONTINUE:
                session.add_message("assistant", "⚠ 已达到自动工作流上限（10步），请检查当前状态后继续。")
        else:
            session.add_message("assistant", reply)

        # Done — stop workflow
        _auto_continue_active = False
        bpy.context.scene.aimm_is_loading = False
        _tag_redraw_all()
        return None


class AIMM_OT_Undo(bpy.types.Operator):
    bl_idname = "aimm.undo"
    bl_label = "撤销"
    def execute(self, context):
        undo()
        _tag_redraw_all()
        return {'FINISHED'}


class AIMM_OT_ClearChat(bpy.types.Operator):
    bl_idname = "aimm.clear_chat"
    bl_label = "清空对话"
    def execute(self, context):
        get_session().clear()
        _tag_redraw_all()
        return {'FINISHED'}


class AIMM_OT_StopWorkflow(bpy.types.Operator):
    bl_idname = "aimm.stop_workflow"
    bl_label = "停止工作流"
    bl_description = "停止 AI 自动工作流"

    def execute(self, context):
        global _stop_requested, _auto_continue_active
        _stop_requested = True
        _auto_continue_active = False
        session = get_session()
        session.add_message("assistant", "⚠ 工作流已被用户停止。")
        _tag_redraw_all()
        return {'FINISHED'}


OPERATOR_CLASSES = [AIMM_OT_SendMessage, AIMM_OT_Undo, AIMM_OT_ClearChat, AIMM_OT_StopWorkflow]
