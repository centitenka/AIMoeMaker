# ui/node_header.py
"""
Header extension for the AIMoeMaker node editor.
Adds an 'Execute' button to the node editor header when our tree type is active.
"""
import bpy


def draw_aimm_node_header(self, context):
    """Append to NODE_HT_header for AIMoeMaker node trees."""
    if (context.space_data
            and hasattr(context.space_data, 'node_tree')
            and context.space_data.node_tree
            and context.space_data.node_tree.bl_idname == "AIMoeMakerNodeTree"):
        layout = self.layout
        layout.separator()
        layout.operator("aimm.execute_node_tree", text="执行节点图", icon='PLAY')
