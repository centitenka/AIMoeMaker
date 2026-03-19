# ui/node_eval.py
"""
Node graph evaluation engine.
Traverses the node tree following connections and executes each node's command.
"""
from typing import Optional


def evaluate_node_tree(node_tree) -> dict:
    """
    Evaluate all nodes in a node tree in topological order.

    Starting from nodes with no model input connections (source nodes),
    follows the graph forward through connections, executing each node.

    Returns: {"success": bool, "results": list[dict], "errors": list[str]}
    """
    if node_tree is None:
        return {"success": False, "results": [], "errors": ["未找到节点树"]}

    # Build adjacency: for each node, find what nodes feed into it
    nodes = list(node_tree.nodes)
    if not nodes:
        return {"success": True, "results": [], "errors": []}

    # Topological sort using link connections
    sorted_nodes = _topological_sort(nodes, node_tree.links)

    results = []
    errors = []

    # Get model state from session
    from .operators import get_session, get_engine
    session = get_session()

    context_dict = {
        "model_state": session.model_state,
        "bpy_available": True,
    }
    engine = get_engine()

    from ..utils.undo import push_undo
    push_undo("节点图执行")

    for node in sorted_nodes:
        action = ""
        params = {}

        # Get command info from node
        if hasattr(node, "get_command_action"):
            action = node.get_command_action()
            params = node.get_command_params() if hasattr(node, "get_command_params") else {}

        if not action:
            continue

        # Execute the command
        result = engine.execute(action, params, context_dict)
        result["node_name"] = node.bl_label
        results.append(result)

        if not result.get("success", False):
            errors.append(f"节点「{node.bl_label}」执行失败: {result.get('error', '未知错误')}")
            # Continue executing other branches, don't stop entirely

    return {
        "success": len(errors) == 0,
        "results": results,
        "errors": errors,
        "node_count": len(sorted_nodes),
    }


def _topological_sort(nodes: list, links) -> list:
    """
    Sort nodes in execution order: nodes with no input links first,
    then nodes that depend on already-executed nodes.
    """
    # Build dependency graph
    # node -> set of nodes that must execute before it
    dependencies = {node: set() for node in nodes}

    for link in links:
        from_node = link.from_node
        to_node = link.to_node
        if from_node in dependencies and to_node in dependencies:
            dependencies[to_node].add(from_node)

    sorted_list = []
    visited = set()

    def visit(node):
        if node in visited:
            return
        visited.add(node)
        for dep in dependencies.get(node, set()):
            visit(dep)
        sorted_list.append(node)

    for node in nodes:
        visit(node)

    return sorted_list


def find_source_nodes(node_tree) -> list:
    """Find nodes with no model input connections (starting points)."""
    if node_tree is None:
        return []

    nodes_with_input = set()
    for link in node_tree.links:
        nodes_with_input.add(link.to_node)

    return [n for n in node_tree.nodes if n not in nodes_with_input]


def get_execution_order(node_tree) -> list[str]:
    """Get the execution order as a list of node labels (for UI display)."""
    if node_tree is None:
        return []

    sorted_nodes = _topological_sort(list(node_tree.nodes), node_tree.links)
    return [n.bl_label for n in sorted_nodes if hasattr(n, "get_command_action")]


# --- Blender Operator ---

try:
    import bpy
    _bpy_available = True
except ImportError:
    _bpy_available = False

if _bpy_available:
    class AIMM_OT_ExecuteNodeTree(bpy.types.Operator):
        bl_idname = "aimm.execute_node_tree"
        bl_label = "执行节点图"
        bl_description = "按连接顺序执行所有节点"
        bl_options = {'REGISTER', 'UNDO'}

        @classmethod
        def poll(cls, context):
            return (context.space_data
                    and hasattr(context.space_data, 'node_tree')
                    and context.space_data.node_tree
                    and context.space_data.node_tree.bl_idname == "AIMoeMakerNodeTree")

        def execute(self, context):
            node_tree = context.space_data.node_tree
            result = evaluate_node_tree(node_tree)

            if result["success"]:
                self.report({'INFO'}, f"节点图执行完成: {result['node_count']} 个节点")
            else:
                for err in result["errors"]:
                    self.report({'ERROR'}, err)

            return {'FINISHED'}

    NODE_EVAL_CLASSES = [AIMM_OT_ExecuteNodeTree]
else:
    NODE_EVAL_CLASSES = []
