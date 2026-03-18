def push_undo(label: str):
    try:
        import bpy
        bpy.ops.ed.undo_push(message=f"AIMoeMaker: {label}")
    except Exception:
        pass

def undo():
    try:
        import bpy
        bpy.ops.ed.undo()
    except Exception:
        pass

def redo():
    try:
        import bpy
        bpy.ops.ed.redo()
    except Exception:
        pass
