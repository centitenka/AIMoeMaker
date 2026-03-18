"""
Body commands: create base body, set height, adjust proportions.
All bpy operations are guarded by context["bpy_available"].
"""
from __future__ import annotations

from commands.base import BaseCommand
from core.model_state import BodyState


# ---------------------------------------------------------------------------
# Preset definitions
# ---------------------------------------------------------------------------

BODY_PRESETS: dict[str, dict] = {
    "loli": {
        "body_type": "loli",
        "height": 145.0,
        "bust": 0.2,
        "waist": 0.35,
        "hip": 0.3,
        "head_ratio": 0.7,
    },
    "teen": {
        "body_type": "teen",
        "height": 155.0,
        "bust": 0.4,
        "waist": 0.45,
        "hip": 0.45,
        "head_ratio": 0.55,
    },
    "default": {
        "body_type": "default",
        "height": 158.0,
        "bust": 0.5,
        "waist": 0.5,
        "hip": 0.5,
        "head_ratio": 0.5,
    },
    "adult": {
        "body_type": "adult",
        "height": 165.0,
        "bust": 0.6,
        "waist": 0.5,
        "hip": 0.6,
        "head_ratio": 0.45,
    },
}

HEIGHT_MIN = 50.0
HEIGHT_MAX = 300.0
PROPORTION_MIN = 0.0
PROPORTION_MAX = 1.0


# ---------------------------------------------------------------------------
# CreateBaseBody
# ---------------------------------------------------------------------------

class CreateBaseBody(BaseCommand):
    action = "create_base_body"

    def execute(self, params: dict, context: dict) -> dict:
        state = context["model_state"]
        body_type = params.get("body_type", "default")

        # Start from the preset (or "default" if unknown type)
        preset = BODY_PRESETS.get(body_type, BODY_PRESETS["default"])

        # Apply preset values to body state
        state.body.body_type = preset["body_type"]
        state.body.height = preset["height"]
        state.body.bust = preset["bust"]
        state.body.waist = preset["waist"]
        state.body.hip = preset["hip"]
        state.body.head_ratio = preset["head_ratio"]

        # Allow explicit height override from params
        if "height" in params:
            height = float(params["height"])
            if not (HEIGHT_MIN <= height <= HEIGHT_MAX):
                return {
                    "success": False,
                    "error": f"身高超出范围: 请在 {HEIGHT_MIN}–{HEIGHT_MAX} cm 之间",
                }
            state.body.height = height

        if context.get("bpy_available", False):
            self._create_mesh(state, context)

        return {
            "success": True,
            "message": f"已创建基础身体: {body_type}, 身高 {state.body.height}cm",
        }

    def _create_mesh(self, state, context) -> None:  # pragma: no cover
        """Create the base mesh in Blender (only called when bpy is available)."""
        from blender_ops.body_ops import create_body
        create_body(state.body.height, state.body.body_type, state.body.bust, state.body.waist, state.body.hip, state.body.head_ratio)


# ---------------------------------------------------------------------------
# SetHeight
# ---------------------------------------------------------------------------

class SetHeight(BaseCommand):
    action = "set_height"

    def execute(self, params: dict, context: dict) -> dict:
        state = context["model_state"]
        height = float(params.get("height", state.body.height))

        if not (HEIGHT_MIN <= height <= HEIGHT_MAX):
            return {
                "success": False,
                "error": f"身高超出范围: 请在 {HEIGHT_MIN}–{HEIGHT_MAX} cm 之间",
            }

        state.body.height = height

        if context.get("bpy_available", False):
            self._apply_height(state, context)

        return {
            "success": True,
            "message": f"身高已设置为 {height}cm",
        }

    def _apply_height(self, state, context) -> None:  # pragma: no cover
        """Apply height scaling in Blender."""
        from blender_ops.body_ops import apply_height
        apply_height(state.body.height)


# ---------------------------------------------------------------------------
# AdjustProportions
# ---------------------------------------------------------------------------

class AdjustProportions(BaseCommand):
    action = "adjust_proportions"

    _PROPORTION_FIELDS = ("bust", "waist", "hip", "head_ratio")

    def execute(self, params: dict, context: dict) -> dict:
        state = context["model_state"]

        for field in self._PROPORTION_FIELDS:
            if field in params:
                value = float(params[field])
                if not (PROPORTION_MIN <= value <= PROPORTION_MAX):
                    return {
                        "success": False,
                        "error": (
                            f"'{field}' 超出范围: 请在 {PROPORTION_MIN}–{PROPORTION_MAX} 之间"
                        ),
                    }
                setattr(state.body, field, value)

        if context.get("bpy_available", False):
            self._apply_proportions(state, context)

        return {
            "success": True,
            "message": "体型比例已更新",
        }

    def _apply_proportions(self, state, context) -> None:  # pragma: no cover
        """Apply proportion shape keys in Blender."""
        from blender_ops.body_ops import create_body
        create_body(state.body.height, state.body.body_type, state.body.bust, state.body.waist, state.body.hip, state.body.head_ratio)


# ---------------------------------------------------------------------------
# Export list
# ---------------------------------------------------------------------------

BODY_COMMANDS = [CreateBaseBody, SetHeight, AdjustProportions]
