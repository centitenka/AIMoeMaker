import bpy

class AIMoeMakerPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__.rsplit('.', 1)[0] if __package__ and '.' in __package__ else (__package__ or "AIMoeMaker")

    api_key: bpy.props.StringProperty(name="API Key", description="AI 服务的 API Key", subtype='PASSWORD', default="")
    api_endpoint: bpy.props.StringProperty(name="API 端点", description="OpenAI 兼容的 API 端点 URL", default="https://api.openai.com/v1/chat/completions")
    model_name: bpy.props.StringProperty(name="模型名称", description="使用的 AI 模型名称", default="gpt-4o")
    max_tokens: bpy.props.IntProperty(name="最大 Token 数", default=2048, min=256, max=16384)
    temperature: bpy.props.FloatProperty(name="温度", default=0.7, min=0.0, max=2.0)

    def draw(self, context):
        layout = self.layout
        layout.label(text="AI 服务配置", icon='SETTINGS')
        box = layout.box()
        box.prop(self, "api_endpoint")
        box.prop(self, "api_key")
        box.prop(self, "model_name")
        box = layout.box()
        box.label(text="高级设置")
        box.prop(self, "max_tokens")
        box.prop(self, "temperature")

PREFERENCE_CLASSES = [AIMoeMakerPreferences]
