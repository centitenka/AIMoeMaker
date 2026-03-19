"""
Post-step validation hooks.

After each command executes successfully, relevant validators run to check
model state consistency and (when available) Blender scene integrity.
Validators return non-blocking warnings that are surfaced to the user.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


# ---------------------------------------------------------------------------
# Validation result
# ---------------------------------------------------------------------------

@dataclass
class ValidationIssue:
    level: str  # "info", "warning", "error"
    message: str


@dataclass
class StepValidationResult:
    passed: bool = True
    issues: list[ValidationIssue] = field(default_factory=list)

    def add(self, level: str, message: str):
        self.issues.append(ValidationIssue(level=level, message=message))
        if level == "error":
            self.passed = False

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "issues": [{"level": i.level, "message": i.message} for i in self.issues],
        }


# ---------------------------------------------------------------------------
# Individual validator functions
# ---------------------------------------------------------------------------
# Signature: (action, params, result, context) -> None
# They mutate the StepValidationResult passed via context["_vr"].

def _validate_body(action: str, params: dict, result: dict, context: dict):
    """Check body state consistency after body commands."""
    vr: StepValidationResult = context["_vr"]
    state = context["model_state"]
    body = state.body

    if body.height < 100 or body.height > 200:
        vr.add("warning", f"身高 {body.height}cm 偏离常规范围(100-200cm)，模型比例可能异常")

    for prop in ("bust", "waist", "hip", "head_ratio"):
        val = getattr(body, prop, 0.5)
        if val <= 0.05 or val >= 0.95:
            vr.add("warning", f"体型参数 {prop}={val:.2f} 接近极端值，可能导致网格变形")

    # bpy scene check
    if context.get("bpy_available", False):
        try:
            from ..blender_ops.utils import find_aimm_object
            obj = find_aimm_object("body")
            if obj is None:
                vr.add("error", "Blender场景中未找到身体网格对象")
            elif obj.type != "MESH":
                vr.add("error", "身体对象类型不是MESH")
            elif len(obj.data.vertices) == 0:
                vr.add("error", "身体网格顶点数为0")
        except Exception as e:
            vr.add("warning", f"场景检测失败: {e}")


def _validate_face(action: str, params: dict, result: dict, context: dict):
    """Check face state after face commands."""
    vr: StepValidationResult = context["_vr"]
    state = context["model_state"]
    face = state.face
    if face is None:
        return

    from ..commands.face import EYE_SHAPES, FACE_SHAPES
    if hasattr(face, "eye_shape") and face.eye_shape not in EYE_SHAPES:
        vr.add("warning", f"眼型 '{face.eye_shape}' 不在标准列表中，可能无对应模型")
    if face.face_shape not in FACE_SHAPES:
        vr.add("warning", f"脸型 '{face.face_shape}' 不在标准列表中")

    # Validate hex color
    color = getattr(face, "eye_color", "")
    if color and not _is_valid_hex(color):
        vr.add("error", f"瞳色 '{color}' 不是有效的十六进制颜色")


def _validate_hair(action: str, params: dict, result: dict, context: dict):
    """Check hair state after hair commands."""
    vr: StepValidationResult = context["_vr"]
    state = context["model_state"]
    hair = state.hair
    if hair is None:
        return

    from ..commands.hair import HAIR_STYLES
    if hair.style not in HAIR_STYLES:
        vr.add("warning", f"发型 '{hair.style}' 不在标准列表中，可能无对应模型")

    for c in hair.colors:
        if not _is_valid_hex(c):
            vr.add("error", f"头发颜色 '{c}' 不是有效的十六进制颜色")

    if context.get("bpy_available", False):
        try:
            from ..blender_ops.utils import find_aimm_object
            obj = find_aimm_object("hair")
            if obj is None:
                vr.add("warning", "Blender场景中未找到头发网格对象")
        except Exception:
            pass


def _validate_clothing(action: str, params: dict, result: dict, context: dict):
    """Check clothing state after clothing commands."""
    vr: StepValidationResult = context["_vr"]
    state = context["model_state"]

    # Check duplicate slots
    slots = [c.slot for c in state.clothing]
    seen = set()
    for s in slots:
        if s in seen:
            vr.add("warning", f"存在多件服装占用相同部位 '{s}'，可能导致穿模")
        seen.add(s)

    for i, item in enumerate(state.clothing):
        if item.color and not _is_valid_hex(item.color):
            vr.add("warning", f"服装[{i}] 颜色 '{item.color}' 不是有效的十六进制颜色")


def _validate_skeleton(action: str, params: dict, result: dict, context: dict):
    """Check skeleton after skeleton commands."""
    vr: StepValidationResult = context["_vr"]
    state = context["model_state"]

    if not getattr(state.skeleton, "is_configured", False):
        vr.add("info", "骨骼尚未配置，导出前需要 setup_skeleton")
        return

    if context.get("bpy_available", False):
        try:
            from ..blender_ops.utils import find_aimm_object
            arm = find_aimm_object("skeleton")
            if arm is None:
                vr.add("error", "Blender场景中未找到骨骼对象")
            else:
                from ..pipeline.skeleton_setup import REQUIRED_BONES
                existing = {b.name for b in arm.data.bones}
                missing = set(REQUIRED_BONES) - existing
                if missing:
                    vr.add("warning", f"缺少 {len(missing)} 根必要MMD骨骼: {', '.join(sorted(missing))}")
                if len(existing) == 0:
                    vr.add("error", "骨骼对象内没有骨骼")
        except Exception as e:
            vr.add("warning", f"骨骼场景检测失败: {e}")


def _validate_physics(action: str, params: dict, result: dict, context: dict):
    """Check physics setup consistency."""
    vr: StepValidationResult = context["_vr"]
    state = context["model_state"]

    if not getattr(state.skeleton, "is_configured", False):
        vr.add("warning", "物理系统需要骨骼支持，建议先配置骨骼")

    if action == "setup_hair_physics" and (state.hair is None or not state.hair.physics_enabled):
        vr.add("warning", "头发物理标记未正确设置")

    if action == "setup_cloth_physics":
        idx = params.get("index", 0)
        if 0 <= idx < len(state.clothing) and not state.clothing[idx].physics_enabled:
            vr.add("warning", "服装物理标记未正确设置")

    if context.get("bpy_available", False):
        try:
            from ..pipeline.physics_setup import verify_physics
            phys_result = verify_physics()
            for w in phys_result.get("warnings", []):
                vr.add("info", w)
        except Exception:
            pass


def _validate_morph(action: str, params: dict, result: dict, context: dict):
    """Check morph state after morph commands."""
    vr: StepValidationResult = context["_vr"]
    state = context["model_state"]

    expressions = getattr(state.morphs, "expressions", [])
    if len(expressions) > 0:
        # Check for required MMD morphs
        required = {"まばたき", "あ"}
        present = set(expressions)
        missing = required - present
        if missing:
            vr.add("info", f"尚缺必要MMD表情: {', '.join(missing)}（导出前需要）")

    if context.get("bpy_available", False):
        try:
            from ..blender_ops.utils import find_aimm_object
            body = find_aimm_object("body")
            if body and body.data.shape_keys:
                sk_names = {sk.name for sk in body.data.shape_keys.key_blocks}
                state_exprs = set(expressions)
                orphaned = state_exprs - sk_names
                if orphaned:
                    vr.add("warning", f"状态中记录的表情在场景中不存在: {', '.join(orphaned)}")
        except Exception:
            pass


def _validate_weight_paint(action: str, params: dict, result: dict, context: dict):
    """Check weight paint coverage after auto_weight_paint."""
    vr: StepValidationResult = context["_vr"]

    if not context.get("bpy_available", False):
        return

    try:
        from ..blender_ops.utils import find_aimm_object
        from ..pipeline.weight_paint import verify_weights
        body = find_aimm_object("body")
        arm = find_aimm_object("skeleton")
        if body and arm:
            wr = verify_weights(body, arm)
            coverage = wr.get("coverage", "100.0%")
            unweighted = wr.get("unweighted_count", 0)
            if unweighted > 0:
                vr.add("warning", f"权重覆盖率 {coverage}，仍有 {unweighted} 个未绑定顶点")
            else:
                vr.add("info", f"权重覆盖率 {coverage}")
    except Exception as e:
        vr.add("warning", f"权重检测失败: {e}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_valid_hex(color: str) -> bool:
    """Check if a string is a valid hex color like #RRGGBB or #RGB."""
    if not isinstance(color, str):
        return False
    c = color.lstrip("#")
    if len(c) not in (3, 6):
        return False
    try:
        int(c, 16)
        return True
    except ValueError:
        return False


# ---------------------------------------------------------------------------
# Registry: action -> list of validator functions
# ---------------------------------------------------------------------------

_ACTION_VALIDATORS: dict[str, list[Callable]] = {
    # Body
    "create_base_body": [_validate_body],
    "set_height": [_validate_body],
    "adjust_proportions": [_validate_body],
    # Face
    "set_eye_shape": [_validate_face],
    "set_eye_color": [_validate_face],
    "adjust_face_shape": [_validate_face],
    # Hair
    "add_hair": [_validate_hair],
    "modify_hair_style": [_validate_hair],
    "set_hair_color": [_validate_hair],
    # Clothing
    "add_clothing": [_validate_clothing],
    "modify_clothing": [_validate_clothing],
    "set_fabric_material": [_validate_clothing],
    # Skeleton
    "setup_skeleton": [_validate_skeleton],
    "auto_weight_paint": [_validate_skeleton, _validate_weight_paint],
    # Physics
    "setup_hair_physics": [_validate_physics],
    "setup_cloth_physics": [_validate_physics],
    # Morphs
    "create_morph": [_validate_morph],
    "add_expression_set": [_validate_morph],
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_step_validation(action: str, params: dict, result: dict, context: dict) -> StepValidationResult:
    """
    Run all validators registered for *action*.

    Called by CommandEngine after a successful command execution.
    Returns a StepValidationResult with any issues found.
    """
    vr = StepValidationResult()
    validators = _ACTION_VALIDATORS.get(action)
    if not validators:
        return vr

    # Inject the validation result into context for validators to mutate
    ctx = dict(context)
    ctx["_vr"] = vr

    for fn in validators:
        try:
            fn(action, params, result, ctx)
        except Exception as e:
            vr.add("warning", f"验证器异常({fn.__name__}): {e}")

    return vr
