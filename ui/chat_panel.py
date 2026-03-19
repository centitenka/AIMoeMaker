import bpy
from .operators import get_session


def _wrap_text(text, width=40):
    """Wrap text into multiple lines for Blender UI labels."""
    lines = []
    for paragraph in text.split("\n"):
        if not paragraph:
            lines.append("")
            continue
        while len(paragraph) > width:
            # Try to break at a space
            break_at = paragraph.rfind(" ", 0, width)
            if break_at <= 0:
                break_at = width
            lines.append(paragraph[:break_at])
            paragraph = paragraph[break_at:].lstrip()
        lines.append(paragraph)
    return lines or [""]


class AIMM_PT_ChatPanel(bpy.types.Panel):
    bl_label = "AIMoeMaker"
    bl_idname = "AIMM_PT_ChatPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "AIMoeMaker"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        session = get_session()

        chat_box = layout.box()
        chat_box.label(text="对话", icon='TEXT')
        if not session.conversation:
            chat_box.label(text="描述你想创建的角色吧！", icon='INFO')
        else:
            for msg in session.conversation[-10:]:
                content = msg["content"]
                if msg["role"] == "user":
                    prefix, icon = "你", 'USER'
                else:
                    prefix, icon = "AI", 'LIGHT'
                # Split long text into wrapped lines
                lines = _wrap_text(f"{prefix}: {content}", width=40)
                for i, line in enumerate(lines):
                    chat_box.label(text=line, icon=icon if i == 0 else 'BLANK1')

        if scene.aimm_is_loading:
            from .operators import _auto_continue_active, _auto_continue_count, _MAX_AUTO_CONTINUE
            if _auto_continue_active:
                layout.label(text=f"AI 自动工作中... 步骤 {_auto_continue_count}/{_MAX_AUTO_CONTINUE}", icon='TIME')
                layout.operator("aimm.stop_workflow", text="停止", icon='CANCEL')
            else:
                layout.label(text="AI 思考中...", icon='TIME')

        input_box = layout.box()
        input_box.prop(scene, "aimm_chat_input", text="")
        row = input_box.row(align=True)
        row.operator("aimm.send_message", text="发送", icon='PLAY')
        row.operator("aimm.undo", text="撤销", icon='LOOP_BACK')
        row.operator("aimm.clear_chat", text="清空", icon='TRASH')

        state_box = layout.box()
        state_box.label(text="当前模型状态", icon='OBJECT_DATA')
        for line in session.model_state.to_summary().split("\n"):
            state_box.label(text=line)


PANEL_CLASSES = [AIMM_PT_ChatPanel]
