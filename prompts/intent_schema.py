"""
Intent schema for parsing AI responses in AIMoeMaker.

Defines the contract between AIMoeMaker and the AI LLM.
The AI returns JSON with reply + intents, and this module parses it.
"""

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


KNOWN_COMMANDS = {
    # Body commands
    "create_base_body",
    "adjust_proportions",
    "set_height",
    # Head / face commands
    "set_head_shape",
    "set_eye_size",
    "set_eye_color",
    "set_hair_style",
    "set_hair_color",
    # Clothing commands
    "add_clothing",
    "remove_clothing",
    "set_clothing_color",
    # Pose commands
    "set_pose",
    "reset_pose",
    # Expression commands
    "set_expression",
    # Material / shader commands
    "set_skin_tone",
    "apply_material",
    # Scene commands
    "set_background",
    "set_lighting",
    # General
    "undo",
    "redo",
    "save_model",
    "load_model",
    "export_model",
}


@dataclass
class Intent:
    """Represents a single parsed intent from the AI response."""
    intent_type: str = "command"
    action: str = ""
    params: Dict[str, Any] = field(default_factory=dict)
    code: Optional[str] = None
    description: Optional[str] = None


@dataclass
class AIResponse:
    """Represents the full parsed AI response."""
    reply: str = ""
    intents: List[Intent] = field(default_factory=list)
    raw: str = ""
    continue_workflow: bool = False


def _extract_json(text: str) -> Optional[str]:
    """
    Extract a JSON object string from text that may contain code fences
    or surrounding prose.

    Uses json.loads-based validation rather than brace counting.
    Returns the JSON string if found, else None.
    """
    # Try code fences first
    fence_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
    if fence_match:
        candidate = fence_match.group(1).strip()
        try:
            json.loads(candidate)
            return candidate
        except json.JSONDecodeError:
            pass

    # Try to parse JSON starting from each '{' position
    start = 0
    while True:
        idx = text.find('{', start)
        if idx == -1:
            return None
        try:
            obj = json.loads(text[idx:])
            return json.dumps(obj, ensure_ascii=False)
        except json.JSONDecodeError:
            for end_idx in range(len(text) - 1, idx, -1):
                if text[end_idx] == '}':
                    try:
                        json.loads(text[idx:end_idx + 1])
                        return text[idx:end_idx + 1]
                    except json.JSONDecodeError:
                        continue
            start = idx + 1


def _parse_intent(raw_intent: Dict[str, Any]) -> Intent:
    """Parse a single intent dict into an Intent dataclass."""
    return Intent(
        intent_type=raw_intent.get("type", "command"),
        action=raw_intent.get("action", ""),
        params=raw_intent.get("params", {}),
        code=raw_intent.get("code"),
        description=raw_intent.get("description"),
    )


def parse_ai_response(raw_text: str) -> AIResponse:
    """
    Parse the raw AI output into an AIResponse.

    The AI is expected to output JSON with the shape:
        {
            "reply": "<human-readable reply in Chinese>",
            "intents": [
                {
                    "type": "command",
                    "action": "<action_name>",
                    "params": { ... }
                },
                ...
            ]
        }

    If the output is not valid JSON (or cannot be extracted), falls back to
    treating the entire text as a plain reply with no intents.
    """
    json_str = _extract_json(raw_text)

    if json_str is None:
        # Fallback: plain text reply, no intents
        return AIResponse(reply=raw_text, intents=[], raw=raw_text)

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError:
        return AIResponse(reply=raw_text, intents=[], raw=raw_text)

    if not isinstance(data, dict):
        return AIResponse(reply=raw_text, intents=[], raw=raw_text)

    reply = data.get("reply", "")
    raw_intents = data.get("intents", [])
    continue_workflow = bool(data.get("continue", False))

    intents = [_parse_intent(i) for i in raw_intents if isinstance(i, dict)]

    return AIResponse(reply=reply, intents=intents, raw=raw_text, continue_workflow=continue_workflow)
