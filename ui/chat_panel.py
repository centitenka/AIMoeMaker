import bpy
from ui.operators import get_session


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
                row = chat_box.row()
                if msg["role"] == "user":
                    row.label(text=f"你: {msg['content'][:80]}", icon='USER')
                else:
                    row.label(text=f"AI: {msg['content'][:80]}", icon='LIGHT')

        if scene.aimm_is_loading:
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
