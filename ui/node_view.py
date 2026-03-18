# ui/node_view.py
"""
AIMoeMaker Node View: visual node editor for composing MMD model workflows.

Architecture:
- AIMoeMakerNodeTree: custom node tree type
- AIMoeMakerSocket: data flow socket (carries ModelState reference)
- AIMoeMakerBaseNode: base class for all command nodes
- Node categories for the Add menu
"""
import bpy
from bpy.types import NodeTree, Node, NodeSocket
from nodeitems_utils import NodeCategory, NodeItem


# ============================================================
# Custom Node Tree
# ============================================================

class AIMoeMakerNodeTree(NodeTree):
    """AIMoeMaker 角色建模节点树"""
    bl_idname = "AIMoeMakerNodeTree"
    bl_label = "AIMoeMaker 节点编辑器"
    bl_icon = 'OUTLINER_OB_ARMATURE'


# ============================================================
# Custom Sockets
# ============================================================

class AIMoeMakerModelSocket(NodeSocket):
    """模型数据流 Socket — 在节点间传递模型状态"""
    bl_idname = "AIMoeMakerModelSocket"
    bl_label = "模型"

    def draw(self, context, layout, node, text):
        layout.label(text=text)

    def draw_color(self, context, node):
        return (0.4, 0.8, 0.4, 1.0)  # Green


class AIMoeMakerParamSocket(NodeSocket):
    """参数 Socket — 传递颜色、数值等参数"""
    bl_idname = "AIMoeMakerParamSocket"
    bl_label = "参数"

    default_value: bpy.props.StringProperty(default="")

    def draw(self, context, layout, node, text):
        if self.is_output or self.is_linked:
            layout.label(text=text)
        else:
            layout.prop(self, "default_value", text=text)

    def draw_color(self, context, node):
        return (0.8, 0.6, 0.2, 1.0)  # Orange


# ============================================================
# Base Node Class
# ============================================================

class AIMoeMakerBaseNode(Node):
    """所有 AIMoeMaker 节点的基类"""

    @classmethod
    def poll(cls, ntree):
        return ntree.bl_idname == "AIMoeMakerNodeTree"

    def get_command_action(self) -> str:
        """Override in subclass: return the command action name."""
        return ""

    def get_command_params(self) -> dict:
        """Override in subclass: return command parameters dict."""
        return {}

    def init_sockets(self):
        """Call in init() to set up standard model in/out sockets."""
        self.inputs.new("AIMoeMakerModelSocket", "模型输入")
        self.outputs.new("AIMoeMakerModelSocket", "模型输出")

    def draw_buttons(self, context, layout):
        """Override to draw node-specific UI."""
        pass

    def execute(self, model_state, context_dict) -> dict:
        """Execute this node's command. Called by the evaluation engine."""
        from core.command_engine import CommandEngine
        action = self.get_command_action()
        params = self.get_command_params()
        if not action:
            return {"success": False, "error": "节点未定义指令"}

        # Use the global engine
        from ui.operators import get_engine
        engine = get_engine()
        return engine.execute(action, params, context_dict)


# ============================================================
# Node Categories (for Add menu)
# ============================================================

class AIMM_NODE_CAT_Body(NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == "AIMoeMakerNodeTree"


class AIMM_NODE_CAT_Hair(NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == "AIMoeMakerNodeTree"


class AIMM_NODE_CAT_Face(NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == "AIMoeMakerNodeTree"


class AIMM_NODE_CAT_Clothing(NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == "AIMoeMakerNodeTree"


class AIMM_NODE_CAT_Advanced(NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == "AIMoeMakerNodeTree"


# ============================================================
# Export lists (populated by node_nodes.py after import)
# ============================================================

NODE_TREE_CLASSES = [
    AIMoeMakerNodeTree,
    AIMoeMakerModelSocket,
    AIMoeMakerParamSocket,
]

# Base node class is not registered directly — only subclasses are
NODE_BASE_CLASSES = []  # Populated by register_node_categories()

_node_categories_registered = False


def get_node_categories(node_items_by_category: dict) -> list:
    """
    Build node category list for nodeitems_utils.register_node_categories.

    Args:
        node_items_by_category: dict of {"category_name": [NodeItem, ...]}
    """
    categories = []

    cat_classes = {
        "身体": AIMM_NODE_CAT_Body,
        "头发": AIMM_NODE_CAT_Hair,
        "面部": AIMM_NODE_CAT_Face,
        "服装/配饰": AIMM_NODE_CAT_Clothing,
        "骨骼/物理/导出": AIMM_NODE_CAT_Advanced,
    }

    for cat_name, cat_cls in cat_classes.items():
        items = node_items_by_category.get(cat_name, [])
        if items:
            cat_id = f"AIMM_NODES_{cat_name}"
            categories.append(cat_cls(cat_id, cat_name, items=items))

    return categories


def register_node_categories(node_classes: list, node_items_by_category: dict):
    """Register node categories with Blender."""
    global _node_categories_registered
    import nodeitems_utils

    if _node_categories_registered:
        try:
            nodeitems_utils.unregister_node_categories("AIMM_NODES")
        except Exception:
            pass

    categories = get_node_categories(node_items_by_category)
    if categories:
        nodeitems_utils.register_node_categories("AIMM_NODES", categories)
        _node_categories_registered = True


def unregister_node_categories():
    """Unregister node categories."""
    global _node_categories_registered
    if _node_categories_registered:
        import nodeitems_utils
        try:
            nodeitems_utils.unregister_node_categories("AIMM_NODES")
        except Exception:
            pass
        _node_categories_registered = False
