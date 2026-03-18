# ui/node_nodes.py
"""
Concrete node types for the AIMoeMaker node editor.
Each node maps to one or more commands in the Command Engine.
"""
import bpy
from bpy.types import Node
from nodeitems_utils import NodeItem


# We can't import AIMoeMakerBaseNode at module level because bpy types
# need to be registered first. Use a mixin pattern instead.

def _base_poll(cls, ntree):
    return ntree.bl_idname == "AIMoeMakerNodeTree"


def _init_model_sockets(self, context):
    self.inputs.new("AIMoeMakerModelSocket", "模型输入")
    self.outputs.new("AIMoeMakerModelSocket", "模型输出")


# ============================================================
# Body Nodes
# ============================================================

class AIMM_NODE_CreateBody(Node):
    bl_idname = "AIMM_NODE_CreateBody"
    bl_label = "创建身体"
    bl_icon = 'OUTLINER_OB_ARMATURE'

    body_type: bpy.props.EnumProperty(
        name="体型",
        items=[("loli", "萝莉", ""), ("teen", "少女", ""), ("default", "默认", ""), ("adult", "成人", "")],
        default="default",
    )
    height: bpy.props.FloatProperty(name="身高(cm)", default=158.0, min=50.0, max=300.0)

    @classmethod
    def poll(cls, ntree):
        return _base_poll(cls, ntree)

    def init(self, context):
        _init_model_sockets(self, context)

    def draw_buttons(self, context, layout):
        layout.prop(self, "body_type")
        layout.prop(self, "height")

    def get_command_action(self):
        return "create_base_body"

    def get_command_params(self):
        return {"body_type": self.body_type, "height": self.height}


class AIMM_NODE_AdjustProportions(Node):
    bl_idname = "AIMM_NODE_AdjustProportions"
    bl_label = "调整比例"
    bl_icon = 'MOD_LATTICE'

    bust: bpy.props.FloatProperty(name="胸围", default=0.5, min=0.0, max=1.0)
    waist: bpy.props.FloatProperty(name="腰围", default=0.5, min=0.0, max=1.0)
    hip: bpy.props.FloatProperty(name="臀围", default=0.5, min=0.0, max=1.0)
    head_ratio: bpy.props.FloatProperty(name="头身比", default=0.5, min=0.0, max=1.0)

    @classmethod
    def poll(cls, ntree):
        return _base_poll(cls, ntree)

    def init(self, context):
        _init_model_sockets(self, context)

    def draw_buttons(self, context, layout):
        col = layout.column(align=True)
        col.prop(self, "bust", slider=True)
        col.prop(self, "waist", slider=True)
        col.prop(self, "hip", slider=True)
        col.prop(self, "head_ratio", slider=True)

    def get_command_action(self):
        return "adjust_proportions"

    def get_command_params(self):
        return {"bust": self.bust, "waist": self.waist, "hip": self.hip, "head_ratio": self.head_ratio}


# ============================================================
# Hair Nodes
# ============================================================

class AIMM_NODE_AddHair(Node):
    bl_idname = "AIMM_NODE_AddHair"
    bl_label = "添加头发"
    bl_icon = 'STRANDS'

    hair_style: bpy.props.EnumProperty(
        name="发型",
        items=[
            ("short", "短发", ""), ("long", "长发", ""), ("twintail", "双马尾", ""),
            ("ponytail", "马尾", ""), ("bob", "波波头", ""), ("hime_cut", "公主切", ""),
            ("drill", "钻头卷", ""), ("braid", "辫子", ""), ("odango", "丸子头", ""),
            ("ahoge", "呆毛", ""),
        ],
        default="long",
    )
    hair_color: bpy.props.FloatVectorProperty(
        name="发色", subtype='COLOR', default=(0.1, 0.1, 0.1), min=0.0, max=1.0)
    length: bpy.props.FloatProperty(name="长度", default=0.5, min=0.0, max=1.0)
    gradient: bpy.props.BoolProperty(name="渐变", default=False)

    @classmethod
    def poll(cls, ntree):
        return _base_poll(cls, ntree)

    def init(self, context):
        _init_model_sockets(self, context)

    def draw_buttons(self, context, layout):
        layout.prop(self, "hair_style")
        layout.prop(self, "hair_color")
        layout.prop(self, "length", slider=True)
        layout.prop(self, "gradient")

    def get_command_action(self):
        return "add_hair"

    def get_command_params(self):
        r, g, b = self.hair_color
        hex_color = "#{:02x}{:02x}{:02x}".format(int(r * 255), int(g * 255), int(b * 255))
        return {"style": self.hair_style, "colors": [hex_color], "length": self.length, "gradient": self.gradient}


# ============================================================
# Face Nodes
# ============================================================

class AIMM_NODE_SetEyes(Node):
    bl_idname = "AIMM_NODE_SetEyes"
    bl_label = "设置眼睛"
    bl_icon = 'HIDE_OFF'

    eye_shape: bpy.props.EnumProperty(
        name="眼型",
        items=[("round", "圆形", ""), ("almond", "杏仁", ""), ("cat", "猫眼", ""),
               ("droopy", "下垂", ""), ("tsurime", "上吊", ""), ("tareme", "下吊", "")],
        default="round",
    )
    eye_color: bpy.props.FloatVectorProperty(
        name="瞳色", subtype='COLOR', default=(0.4, 0.2, 0.0), min=0.0, max=1.0)

    @classmethod
    def poll(cls, ntree):
        return _base_poll(cls, ntree)

    def init(self, context):
        _init_model_sockets(self, context)

    def draw_buttons(self, context, layout):
        layout.prop(self, "eye_shape")
        layout.prop(self, "eye_color")

    def get_command_action(self):
        return "set_eye_shape"

    def get_command_params(self):
        r, g, b = self.eye_color
        hex_color = "#{:02x}{:02x}{:02x}".format(int(r * 255), int(g * 255), int(b * 255))
        return {"shape": self.eye_shape, "color": hex_color}


class AIMM_NODE_SetFaceShape(Node):
    bl_idname = "AIMM_NODE_SetFaceShape"
    bl_label = "设置脸型"
    bl_icon = 'MESH_CIRCLE'

    face_shape: bpy.props.EnumProperty(
        name="脸型",
        items=[("oval", "鹅蛋", ""), ("round", "圆脸", ""), ("heart", "心形", ""),
               ("square", "方形", ""), ("diamond", "菱形", "")],
        default="oval",
    )

    @classmethod
    def poll(cls, ntree):
        return _base_poll(cls, ntree)

    def init(self, context):
        _init_model_sockets(self, context)

    def draw_buttons(self, context, layout):
        layout.prop(self, "face_shape")

    def get_command_action(self):
        return "adjust_face_shape"

    def get_command_params(self):
        return {"shape": self.face_shape}


# ============================================================
# Clothing Nodes
# ============================================================

class AIMM_NODE_AddClothing(Node):
    bl_idname = "AIMM_NODE_AddClothing"
    bl_label = "添加服装"
    bl_icon = 'MATCLOTH'

    clothing_type: bpy.props.EnumProperty(
        name="类型",
        items=[
            ("shirt", "衬衫", ""), ("t_shirt", "T恤", ""), ("blouse", "女衬衫", ""),
            ("jacket", "夹克", ""), ("skirt", "短裙", ""), ("long_skirt", "长裙", ""),
            ("dress", "连衣裙", ""), ("gothic_dress", "哥特裙", ""),
            ("school_uniform", "校服", ""), ("shorts", "短裤", ""), ("pants", "长裤", ""),
        ],
        default="dress",
    )
    clothing_color: bpy.props.FloatVectorProperty(
        name="颜色", subtype='COLOR', default=(0.8, 0.8, 0.8), min=0.0, max=1.0)

    @classmethod
    def poll(cls, ntree):
        return _base_poll(cls, ntree)

    def init(self, context):
        _init_model_sockets(self, context)

    def draw_buttons(self, context, layout):
        layout.prop(self, "clothing_type")
        layout.prop(self, "clothing_color")

    def get_command_action(self):
        return "add_clothing"

    def get_command_params(self):
        r, g, b = self.clothing_color
        hex_color = "#{:02x}{:02x}{:02x}".format(int(r * 255), int(g * 255), int(b * 255))
        return {"type": self.clothing_type, "color": hex_color}


class AIMM_NODE_AddAccessory(Node):
    bl_idname = "AIMM_NODE_AddAccessory"
    bl_label = "添加配饰"
    bl_icon = 'LINKED'

    accessory_type: bpy.props.StringProperty(name="类型", default="ribbon")
    scale: bpy.props.FloatProperty(name="大小", default=1.0, min=0.1, max=5.0)

    @classmethod
    def poll(cls, ntree):
        return _base_poll(cls, ntree)

    def init(self, context):
        _init_model_sockets(self, context)

    def draw_buttons(self, context, layout):
        layout.prop(self, "accessory_type")
        layout.prop(self, "scale")

    def get_command_action(self):
        return "add_accessory"

    def get_command_params(self):
        return {"type": self.accessory_type, "scale": self.scale}


# ============================================================
# Advanced Nodes (skeleton, physics, morph, export)
# ============================================================

class AIMM_NODE_SetupSkeleton(Node):
    bl_idname = "AIMM_NODE_SetupSkeleton"
    bl_label = "配置骨骼"
    bl_icon = 'ARMATURE_DATA'

    @classmethod
    def poll(cls, ntree):
        return _base_poll(cls, ntree)

    def init(self, context):
        _init_model_sockets(self, context)

    def get_command_action(self):
        return "setup_skeleton"

    def get_command_params(self):
        return {}


class AIMM_NODE_SetupPhysics(Node):
    bl_idname = "AIMM_NODE_SetupPhysics"
    bl_label = "设置物理"
    bl_icon = 'PHYSICS'

    physics_target: bpy.props.EnumProperty(
        name="目标",
        items=[("hair", "头发", ""), ("cloth", "服装", "")],
        default="hair",
    )
    stiffness: bpy.props.FloatProperty(name="刚度", default=0.5, min=0.0, max=1.0)
    damping: bpy.props.FloatProperty(name="阻尼", default=0.3, min=0.0, max=1.0)

    @classmethod
    def poll(cls, ntree):
        return _base_poll(cls, ntree)

    def init(self, context):
        _init_model_sockets(self, context)

    def draw_buttons(self, context, layout):
        layout.prop(self, "physics_target")
        layout.prop(self, "stiffness", slider=True)
        layout.prop(self, "damping", slider=True)

    def get_command_action(self):
        if self.physics_target == "hair":
            return "setup_hair_physics"
        return "setup_cloth_physics"

    def get_command_params(self):
        return {"stiffness": self.stiffness, "damping": self.damping}


class AIMM_NODE_AddExpressions(Node):
    bl_idname = "AIMM_NODE_AddExpressions"
    bl_label = "添加表情"
    bl_icon = 'SHAPEKEY_DATA'

    preset: bpy.props.EnumProperty(
        name="预设",
        items=[("standard", "MMD标准表情集", "")],
        default="standard",
    )

    @classmethod
    def poll(cls, ntree):
        return _base_poll(cls, ntree)

    def init(self, context):
        _init_model_sockets(self, context)

    def draw_buttons(self, context, layout):
        layout.prop(self, "preset")

    def get_command_action(self):
        return "add_expression_set"

    def get_command_params(self):
        return {"preset": self.preset}


class AIMM_NODE_ExportPMX(Node):
    bl_idname = "AIMM_NODE_ExportPMX"
    bl_label = "导出 PMX"
    bl_icon = 'EXPORT'

    filepath: bpy.props.StringProperty(name="路径", subtype='FILE_PATH', default="//model.pmx")

    @classmethod
    def poll(cls, ntree):
        return _base_poll(cls, ntree)

    def init(self, context):
        self.inputs.new("AIMoeMakerModelSocket", "模型输入")
        # No output — terminal node

    def draw_buttons(self, context, layout):
        layout.prop(self, "filepath")

    def get_command_action(self):
        return "export_pmx"

    def get_command_params(self):
        return {"path": self.filepath}


# ============================================================
# All node classes and category mapping
# ============================================================

ALL_NODE_CLASSES = [
    AIMM_NODE_CreateBody,
    AIMM_NODE_AdjustProportions,
    AIMM_NODE_AddHair,
    AIMM_NODE_SetEyes,
    AIMM_NODE_SetFaceShape,
    AIMM_NODE_AddClothing,
    AIMM_NODE_AddAccessory,
    AIMM_NODE_SetupSkeleton,
    AIMM_NODE_SetupPhysics,
    AIMM_NODE_AddExpressions,
    AIMM_NODE_ExportPMX,
]

NODE_ITEMS_BY_CATEGORY = {
    "身体": [
        NodeItem("AIMM_NODE_CreateBody"),
        NodeItem("AIMM_NODE_AdjustProportions"),
    ],
    "头发": [
        NodeItem("AIMM_NODE_AddHair"),
    ],
    "面部": [
        NodeItem("AIMM_NODE_SetEyes"),
        NodeItem("AIMM_NODE_SetFaceShape"),
    ],
    "服装/配饰": [
        NodeItem("AIMM_NODE_AddClothing"),
        NodeItem("AIMM_NODE_AddAccessory"),
    ],
    "骨骼/物理/导出": [
        NodeItem("AIMM_NODE_SetupSkeleton"),
        NodeItem("AIMM_NODE_SetupPhysics"),
        NodeItem("AIMM_NODE_AddExpressions"),
        NodeItem("AIMM_NODE_ExportPMX"),
    ],
}
