# AIMoeMaker Phase 1: Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the foundational loop — user types natural language in Blender sidebar → AI responds with structured intents → Command Engine creates/modifies a basic 3D body in the viewport.

**Architecture:** Blender addon with N-panel Chat UI → Session Manager → AI Provider (OpenAI-compatible first) → Intent Router → Command Engine. All AI calls are async via threading to avoid freezing Blender UI. State tracked in ModelState dataclass, persisted to JSON.

**Tech Stack:** Python 3.11+, Blender 4.2+ API (`bpy`), `urllib.request` (HTTP, no external deps), JSON for serialization.

**Spec:** `docs/superpowers/specs/2026-03-18-aimoemaker-design.md`

**Scope:** This is Plan 1 of 3. Covers only the foundation: plugin skeleton, AI provider, intent routing, one command (body), chat UI, and session management. Commands, PMX pipeline, sandbox, and asset manager come in later plans.

---

## File Structure

```
AIMoeMaker/
  __init__.py                  ← Blender addon registration, bl_info
  blender_manifest.toml        ← Blender 4.2 extension manifest
  ai/
    __init__.py
    provider.py                ← AIProvider base class + AIResponse dataclass
    adapters/
      __init__.py
      openai_compat.py         ← OpenAI-compatible adapter (covers OpenAI, custom endpoints, most Chinese LLMs)
  core/
    __init__.py
    session.py                 ← SessionManager: conversation history, model state, project persistence
    intent_router.py           ← Parse AI JSON response, route intents to handlers
    command_engine.py           ← Command registry + dispatch
    model_state.py             ← ModelState dataclass
  commands/
    __init__.py
    base.py                    ← BaseCommand abstract class
    body.py                    ← create_base_body, adjust_proportions, set_height
  ui/
    __init__.py
    chat_panel.py              ← N-panel chat UI (sidebar)
    operators.py               ← Blender operators (send message, undo, etc.)
    preferences.py             ← Addon preferences (API key, endpoint URL, model name)
  prompts/
    __init__.py
    system_prompt.py           ← System prompt text for MMD modeling
    intent_schema.py           ← Intent JSON schema definition + examples
  utils/
    __init__.py
    undo.py                    ← Undo push/pop helpers
  tests/
    __init__.py
    test_model_state.py
    test_intent_schema.py
    test_intent_router.py
    test_command_engine.py
    test_body_command.py
    test_ai_provider.py
    test_session.py
    conftest.py                ← Shared fixtures, bpy mock setup
    run_tests.py               ← Script to run tests via blender --background
```

---

### Task 1: Plugin Skeleton + Blender Registration

**Files:**
- Create: `AIMoeMaker/__init__.py`
- Create: `AIMoeMaker/blender_manifest.toml`

This task sets up the bare minimum for Blender to recognize and enable the addon.

- [ ] **Step 1: Create blender_manifest.toml**

```toml
schema_version = "1.0.0"

id = "ai_moe_maker"
version = "0.1.0"
name = "AIMoeMaker"
tagline = "AI-powered MMD model creation through natural language"
maintainer = "AIMoeMaker Team"
type = "add-on"

[blender_version_min]
major = 4
minor = 2
patch = 0

[permissions]
network = "AI API calls and asset search"
files = "Project save/load and asset management"
```

- [ ] **Step 2: Create __init__.py with bl_info and minimal register/unregister**

```python
# bl_info is a fallback for manual .zip installation.
# When installed via Extensions Platform, blender_manifest.toml takes precedence.
bl_info = {
    "name": "AIMoeMaker",
    "author": "AIMoeMaker Team",
    "version": (0, 1, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > AIMoeMaker",
    "description": "AI驱动的MMD建模助手，通过自然语言对话创建MMD模型",
    "category": "3D View",
}


def register():
    pass


def unregister():
    pass
```

- [ ] **Step 3: Verify addon loads in Blender**

Run: `blender --background --python-expr "import bpy; bpy.ops.preferences.addon_enable(module='AIMoeMaker'); print('ADDON LOADED OK')"`

Expected: `ADDON LOADED OK` printed without errors.

- [ ] **Step 4: Commit**

```bash
cd E:/Inori_Code/Intrest/AIMoeMaker
git init
git add __init__.py blender_manifest.toml
git commit -m "feat: plugin skeleton with Blender 4.2 registration"
```

---

### Task 2: ModelState Dataclass

**Files:**
- Create: `AIMoeMaker/core/__init__.py`
- Create: `AIMoeMaker/core/model_state.py`
- Create: `AIMoeMaker/tests/__init__.py`
- Create: `AIMoeMaker/tests/conftest.py`
- Create: `AIMoeMaker/tests/test_model_state.py`

ModelState tracks the current state of the 3D model being built. Pure Python, no bpy dependency — easy to test.

- [ ] **Step 1: Create test file for ModelState**

```python
# tests/test_model_state.py
import json
from core.model_state import ModelState


def test_default_model_state():
    state = ModelState()
    assert state.body.height == 158.0
    assert state.body.body_type == "default"
    assert state.hair is None
    assert state.clothing == []


def test_model_state_to_dict():
    state = ModelState()
    d = state.to_dict()
    assert d["schema_version"] == 1
    assert d["body"]["height"] == 158.0


def test_model_state_from_dict():
    state = ModelState()
    state.body.height = 165.0
    d = state.to_dict()
    restored = ModelState.from_dict(d)
    assert restored.body.height == 165.0


def test_model_state_summary():
    state = ModelState()
    summary = state.to_summary()
    assert isinstance(summary, str)
    assert "身体" in summary


def test_model_state_to_json_roundtrip():
    state = ModelState()
    state.body.height = 145.0
    state.body.body_type = "loli"
    json_str = json.dumps(state.to_dict(), ensure_ascii=False)
    restored = ModelState.from_dict(json.loads(json_str))
    assert restored.body.height == 145.0
    assert restored.body.body_type == "loli"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd E:/Inori_Code/Intrest/AIMoeMaker && python -m pytest tests/test_model_state.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'core'`

- [ ] **Step 3: Create conftest.py with path setup**

```python
# tests/conftest.py
import sys
import os

# Add the addon root to path so we can import modules directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

- [ ] **Step 4: Implement ModelState**

```python
# core/model_state.py
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BodyState:
    height: float = 158.0
    body_type: str = "default"  # "loli", "teen", "adult"
    head_ratio: float = 1.0
    bust: float = 0.5
    waist: float = 0.5
    hip: float = 0.5


@dataclass
class HairState:
    style: str = "short"
    colors: list[str] = field(default_factory=lambda: ["#000000"])
    length: float = 0.5
    gradient: bool = False
    physics_enabled: bool = True


@dataclass
class FaceState:
    eye_shape: str = "round"
    eye_color: str = "#663300"
    face_shape: str = "oval"


@dataclass
class ClothingItem:
    clothing_type: str = ""
    material: str = ""
    color: str = "#FFFFFF"
    physics_enabled: bool = False


@dataclass
class AccessoryItem:
    accessory_type: str = ""
    position: list[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    scale: float = 1.0


@dataclass
class SkeletonState:
    is_configured: bool = False
    ik_setup: bool = False


@dataclass
class PhysicsState:
    rigid_body_count: int = 0
    joint_count: int = 0


@dataclass
class MorphState:
    expressions: list[str] = field(default_factory=list)


SCHEMA_VERSION = 1


@dataclass
class ModelState:
    body: BodyState = field(default_factory=BodyState)
    hair: Optional[HairState] = None
    face: Optional[FaceState] = None
    clothing: list[ClothingItem] = field(default_factory=list)
    accessories: list[AccessoryItem] = field(default_factory=list)
    skeleton: SkeletonState = field(default_factory=SkeletonState)
    physics: PhysicsState = field(default_factory=PhysicsState)
    morphs: MorphState = field(default_factory=MorphState)

    def to_dict(self) -> dict:
        """Serialize to dict for JSON persistence."""
        def _obj_to_dict(obj):
            if obj is None:
                return None
            if isinstance(obj, (list, tuple)):
                return [_obj_to_dict(item) for item in obj]
            if hasattr(obj, '__dataclass_fields__'):
                return {k: _obj_to_dict(v) for k, v in obj.__dict__.items()}
            return obj

        d = _obj_to_dict(self)
        d["schema_version"] = SCHEMA_VERSION
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "ModelState":
        """Deserialize from dict."""
        state = cls()
        if "body" in d and d["body"]:
            state.body = BodyState(**{k: v for k, v in d["body"].items()
                                      if k in BodyState.__dataclass_fields__})
        if "hair" in d and d["hair"]:
            state.hair = HairState(**{k: v for k, v in d["hair"].items()
                                      if k in HairState.__dataclass_fields__})
        if "face" in d and d["face"]:
            state.face = FaceState(**{k: v for k, v in d["face"].items()
                                      if k in FaceState.__dataclass_fields__})
        if "clothing" in d:
            state.clothing = [ClothingItem(**{k: v for k, v in item.items()
                                              if k in ClothingItem.__dataclass_fields__})
                              for item in d["clothing"]]
        if "accessories" in d:
            state.accessories = [AccessoryItem(**{k: v for k, v in item.items()
                                                  if k in AccessoryItem.__dataclass_fields__})
                                 for item in d["accessories"]]
        if "skeleton" in d and d["skeleton"]:
            state.skeleton = SkeletonState(**{k: v for k, v in d["skeleton"].items()
                                              if k in SkeletonState.__dataclass_fields__})
        if "physics" in d and d["physics"]:
            state.physics = PhysicsState(**{k: v for k, v in d["physics"].items()
                                            if k in PhysicsState.__dataclass_fields__})
        if "morphs" in d and d["morphs"]:
            state.morphs = MorphState(**{k: v for k, v in d["morphs"].items()
                                          if k in MorphState.__dataclass_fields__})
        return state

    def to_summary(self) -> str:
        """Generate a Chinese text summary for AI context injection."""
        parts = []
        parts.append(f"身体: 身高{self.body.height}cm, 体型={self.body.body_type}")
        if self.hair:
            parts.append(f"头发: 发型={self.hair.style}, 颜色={self.hair.colors}")
        else:
            parts.append("头发: 未设置")
        if self.face:
            parts.append(f"面部: 眼型={self.face.eye_shape}, 瞳色={self.face.eye_color}")
        else:
            parts.append("面部: 未设置")
        if self.clothing:
            items = ", ".join(c.clothing_type for c in self.clothing)
            parts.append(f"服装: {items}")
        else:
            parts.append("服装: 无")
        if self.accessories:
            items = ", ".join(a.accessory_type for a in self.accessories)
            parts.append(f"配饰: {items}")
        else:
            parts.append("配饰: 无")
        parts.append(f"骨骼: {'已配置' if self.skeleton.is_configured else '未配置'}")
        return "\n".join(parts)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd E:/Inori_Code/Intrest/AIMoeMaker && python -m pytest tests/test_model_state.py -v`
Expected: All 5 tests PASS

- [ ] **Step 6: Commit**

```bash
git add core/ tests/
git commit -m "feat: ModelState dataclass with serialization and summary"
```

---

### Task 3: Intent Schema + System Prompt

**Files:**
- Create: `AIMoeMaker/prompts/__init__.py`
- Create: `AIMoeMaker/prompts/intent_schema.py`
- Create: `AIMoeMaker/prompts/system_prompt.py`

These define the contract between AIMoeMaker and the AI — what we send and what we expect back.

- [ ] **Step 1: Create intent_schema.py**

```python
# prompts/intent_schema.py
"""
Defines the JSON schema for AI responses and provides validation.
"""
import json
from dataclasses import dataclass, field
from typing import Optional

# All known command actions
KNOWN_COMMANDS = {
    # Body
    "create_base_body", "adjust_proportions", "set_height",
    # Hair (future)
    "add_hair", "modify_hair_style", "set_hair_color",
    # Face (future)
    "set_eye_shape", "set_eye_color", "adjust_face_shape",
    # Clothing (future)
    "add_clothing", "modify_clothing", "set_fabric_material",
    # Accessory (future)
    "add_accessory", "remove_accessory",
    # Skeleton (future)
    "setup_skeleton", "add_bone", "auto_weight_paint",
    # Physics (future)
    "add_physics_body", "setup_hair_physics", "setup_cloth_physics",
    # Morph (future)
    "create_morph", "add_expression_set",
    # Export (future)
    "export_pmx", "validate_pmx",
}


@dataclass
class Intent:
    intent_type: str  # "command", "code", "asset"
    action: str = ""  # command action name
    params: dict = field(default_factory=dict)
    code: str = ""  # for type="code"
    description: str = ""  # human-readable description


@dataclass
class AIResponse:
    reply: str  # Natural language reply to show user
    intents: list[Intent] = field(default_factory=list)
    raw: str = ""  # Raw AI output for debugging


def parse_ai_response(raw_text: str) -> AIResponse:
    """
    Parse the AI's raw text output into a structured AIResponse.
    Expects JSON with "reply" and "intents" fields.
    Falls back to treating the entire text as a reply with no intents.
    """
    # Try to extract JSON from the response
    json_str = _extract_json(raw_text)
    if json_str is None:
        return AIResponse(reply=raw_text, raw=raw_text)

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError:
        return AIResponse(reply=raw_text, raw=raw_text)

    reply = data.get("reply", "")
    intents = []
    for intent_data in data.get("intents", []):
        intent = Intent(
            intent_type=intent_data.get("type", ""),
            action=intent_data.get("action", ""),
            params=intent_data.get("params", {}),
            code=intent_data.get("code", ""),
            description=intent_data.get("description", ""),
        )
        intents.append(intent)

    return AIResponse(reply=reply, intents=intents, raw=raw_text)


def _extract_json(text: str) -> Optional[str]:
    """Extract a JSON object from text that may contain markdown fences or extra text."""
    import re

    # Try to find JSON in code fences first (most reliable)
    fence_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
    if fence_match:
        candidate = fence_match.group(1).strip()
        try:
            json.loads(candidate)
            return candidate
        except json.JSONDecodeError:
            pass

    # Try to parse JSON starting from each '{' position
    # (more robust than brace counting, handles strings with braces correctly)
    start = 0
    while True:
        idx = text.find('{', start)
        if idx == -1:
            return None
        try:
            obj = json.loads(text[idx:])
            # json.loads succeeds even with trailing text in some cases,
            # so re-serialize to get clean JSON
            return json.dumps(obj, ensure_ascii=False)
        except json.JSONDecodeError:
            # Try progressively shorter substrings ending at each '}'
            for end_idx in range(len(text) - 1, idx, -1):
                if text[end_idx] == '}':
                    try:
                        json.loads(text[idx:end_idx + 1])
                        return text[idx:end_idx + 1]
                    except json.JSONDecodeError:
                        continue
            start = idx + 1
```

- [ ] **Step 2: Create system_prompt.py**

```python
# prompts/system_prompt.py
"""
System prompt for the AI when used in MMD modeling context.
"""

SYSTEM_PROMPT_ZH = '''你是 AIMoeMaker 的 AI 建模助手，帮助用户通过自然语言创建 MMD (PMX) 3D 模型。

## 你的职责
- 理解用户对角色外观的描述
- 将描述转化为结构化的建模指令
- 在对话中引导用户逐步完善角色设计

## 输出格式
你必须始终以以下 JSON 格式回复（不要包裹在代码块中）：

{
  "reply": "你对用户说的话（中文，自然友好）",
  "intents": [
    {
      "type": "command",
      "action": "指令名称",
      "params": { "参数名": "参数值" }
    }
  ]
}

## 可用指令

### 身体 (body)
- `create_base_body`: 创建基础体型
  参数: body_type (string: "loli"/"teen"/"adult"), height (float: cm)
- `adjust_proportions`: 调整身体比例
  参数: bust (float: 0-1), waist (float: 0-1), hip (float: 0-1), head_ratio (float: 0.5-1.5)
- `set_height`: 设置身高
  参数: height (float: cm)

## 行为准则
1. 如果用户的描述涉及多个操作，在一次回复中返回多个 intents
2. 如果用户的描述不够明确，在 reply 中提问，intents 留空
3. 回复使用中文，语气友好且专业
4. 当用户首次描述角色时，先创建基础体型

## 当前模型状态
{model_state_summary}
'''


def build_system_prompt(model_state_summary: str) -> str:
    """Build the complete system prompt with current model state injected."""
    return SYSTEM_PROMPT_ZH.replace("{model_state_summary}", model_state_summary)
```

- [ ] **Step 3: Write tests for intent_schema.py**

```python
# tests/test_intent_schema.py
from prompts.intent_schema import parse_ai_response, _extract_json


def test_parse_valid_json():
    raw = '{"reply": "你好", "intents": [{"type": "command", "action": "set_height", "params": {"height": 160}}]}'
    result = parse_ai_response(raw)
    assert result.reply == "你好"
    assert len(result.intents) == 1
    assert result.intents[0].action == "set_height"


def test_parse_json_in_code_fence():
    raw = '```json\n{"reply": "OK", "intents": []}\n```'
    result = parse_ai_response(raw)
    assert result.reply == "OK"
    assert result.intents == []


def test_parse_non_json_fallback():
    raw = "我不太理解你的意思"
    result = parse_ai_response(raw)
    assert result.reply == raw
    assert result.intents == []


def test_parse_json_with_surrounding_text():
    raw = '好的，这是我的回复：\n{"reply": "创建中", "intents": [{"type": "command", "action": "create_base_body", "params": {}}]}\n以上。'
    result = parse_ai_response(raw)
    assert result.reply == "创建中"
    assert len(result.intents) == 1


def test_parse_json_with_braces_in_strings():
    raw = '{"reply": "使用 { 和 } 要小心", "intents": []}'
    result = parse_ai_response(raw)
    assert result.reply == "使用 { 和 } 要小心"


def test_extract_json_returns_none_for_no_json():
    assert _extract_json("hello world") is None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd E:/Inori_Code/Intrest/AIMoeMaker && python -m pytest tests/test_intent_schema.py -v`
Expected: All 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add prompts/ tests/test_intent_schema.py
git commit -m "feat: intent schema parser and MMD system prompt"
```

---

### Task 4: Intent Router

**Files:**
- Create: `AIMoeMaker/core/intent_router.py`
- Create: `AIMoeMaker/tests/test_intent_router.py`

The Intent Router takes a parsed AIResponse and dispatches each intent to the correct handler.

- [ ] **Step 1: Write failing tests**

```python
# tests/test_intent_router.py
from core.intent_router import IntentRouter
from prompts.intent_schema import Intent, AIResponse


def test_router_dispatches_command():
    results = []

    def mock_command_handler(action, params):
        results.append(("command", action, params))
        return {"success": True}

    router = IntentRouter(command_handler=mock_command_handler)
    intent = Intent(intent_type="command", action="create_base_body",
                    params={"body_type": "loli", "height": 145.0})
    response = AIResponse(reply="OK", intents=[intent])

    execution_results = router.execute(response)
    assert len(results) == 1
    assert results[0] == ("command", "create_base_body", {"body_type": "loli", "height": 145.0})
    assert execution_results[0]["success"] is True


def test_router_handles_empty_intents():
    router = IntentRouter(command_handler=lambda a, p: None)
    response = AIResponse(reply="有什么可以帮你的？", intents=[])
    execution_results = router.execute(response)
    assert execution_results == []


def test_router_stops_on_failure():
    call_count = 0

    def failing_handler(action, params):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RuntimeError("模拟失败")
        return {"success": True}

    router = IntentRouter(command_handler=failing_handler)
    intents = [
        Intent(intent_type="command", action="set_height", params={"height": 160}),
        Intent(intent_type="command", action="set_height", params={"height": 170}),
    ]
    response = AIResponse(reply="OK", intents=intents)

    execution_results = router.execute(response)
    assert call_count == 1  # Second intent was NOT executed
    assert execution_results[0]["success"] is False
    assert "模拟失败" in execution_results[0]["error"]


def test_router_unknown_type_skipped():
    router = IntentRouter(command_handler=lambda a, p: {"success": True})
    intent = Intent(intent_type="unknown_type", action="foo")
    response = AIResponse(reply="OK", intents=[intent])

    execution_results = router.execute(response)
    assert len(execution_results) == 1
    assert execution_results[0]["success"] is False
    assert "未知" in execution_results[0]["error"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd E:/Inori_Code/Intrest/AIMoeMaker && python -m pytest tests/test_intent_router.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'core.intent_router'`

- [ ] **Step 3: Implement IntentRouter**

```python
# core/intent_router.py
"""
Routes parsed AI intents to the appropriate handler.
Stops execution on first failure and reports error.
"""
from typing import Callable, Optional
from prompts.intent_schema import AIResponse, Intent


class IntentRouter:
    def __init__(
        self,
        command_handler: Callable[[str, dict], Optional[dict]] = None,
        code_handler: Callable[[str, str], Optional[dict]] = None,
        asset_handler: Callable[[str, dict], Optional[dict]] = None,
    ):
        self._command_handler = command_handler
        self._code_handler = code_handler
        self._asset_handler = asset_handler

    def execute(self, response: AIResponse) -> list[dict]:
        """
        Execute all intents in order. Stops on first failure.
        Returns a list of result dicts, one per attempted intent.
        """
        results = []
        for intent in response.intents:
            result = self._execute_one(intent)
            results.append(result)
            if not result.get("success", False):
                break
        return results

    def _execute_one(self, intent: Intent) -> dict:
        try:
            if intent.intent_type == "command":
                if self._command_handler is None:
                    return {"success": False, "error": "指令处理器未注册"}
                result = self._command_handler(intent.action, intent.params)
                return result if result else {"success": True}

            elif intent.intent_type == "code":
                if self._code_handler is None:
                    return {"success": False, "error": "代码沙箱未注册（将在后续版本实现）"}
                result = self._code_handler(intent.code, intent.description)
                return result if result else {"success": True}

            elif intent.intent_type == "asset":
                if self._asset_handler is None:
                    return {"success": False, "error": "资产管理器未注册（将在后续版本实现）"}
                result = self._asset_handler(intent.action, intent.params)
                return result if result else {"success": True}

            else:
                return {"success": False, "error": f"未知的意图类型: {intent.intent_type}"}

        except Exception as e:
            return {"success": False, "error": str(e)}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd E:/Inori_Code/Intrest/AIMoeMaker && python -m pytest tests/test_intent_router.py -v`
Expected: All 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add core/intent_router.py tests/test_intent_router.py
git commit -m "feat: intent router with command dispatch and failure handling"
```

---

### Task 5: Command Engine + Base Command

**Files:**
- Create: `AIMoeMaker/core/command_engine.py`
- Create: `AIMoeMaker/commands/__init__.py`
- Create: `AIMoeMaker/commands/base.py`
- Create: `AIMoeMaker/tests/test_command_engine.py`

The Command Engine is a registry that maps action names to command classes.

- [ ] **Step 1: Write failing tests**

```python
# tests/test_command_engine.py
import pytest
from core.command_engine import CommandEngine
from commands.base import BaseCommand


class DummyCommand(BaseCommand):
    """A test command that records calls."""
    action = "test_action"
    calls = []

    def execute(self, params: dict, context: dict) -> dict:
        DummyCommand.calls.append(params)
        return {"success": True, "message": "测试指令已执行"}


def test_register_and_execute():
    DummyCommand.calls = []
    engine = CommandEngine()
    engine.register(DummyCommand)

    result = engine.execute("test_action", {"value": 42}, context={})
    assert result["success"] is True
    assert DummyCommand.calls == [{"value": 42}]


def test_unknown_action_fails():
    engine = CommandEngine()
    result = engine.execute("nonexistent", {}, context={})
    assert result["success"] is False
    assert "未知" in result["error"]


def test_command_exception_caught():
    class FailingCommand(BaseCommand):
        action = "fail_action"
        def execute(self, params, context):
            raise ValueError("something broke")

    engine = CommandEngine()
    engine.register(FailingCommand)

    result = engine.execute("fail_action", {}, context={})
    assert result["success"] is False
    assert "something broke" in result["error"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd E:/Inori_Code/Intrest/AIMoeMaker && python -m pytest tests/test_command_engine.py -v`
Expected: FAIL

- [ ] **Step 3: Implement BaseCommand and CommandEngine**

```python
# commands/base.py
from abc import ABC, abstractmethod


class BaseCommand(ABC):
    """Base class for all commands. Subclasses must set `action` and implement `execute`."""
    action: str = ""

    @abstractmethod
    def execute(self, params: dict, context: dict) -> dict:
        """
        Execute the command.
        Args:
            params: Parameters from the AI intent
            context: Dict containing at minimum {"model_state": ModelState}
        Returns:
            Dict with at least {"success": bool}, optionally {"message": str, "error": str}
        """
        ...
```

```python
# core/command_engine.py
"""
Command registry and dispatcher.
Maps action names to BaseCommand subclasses.
"""
from typing import Type
from commands.base import BaseCommand


class CommandEngine:
    def __init__(self):
        self._commands: dict[str, BaseCommand] = {}

    def register(self, command_cls: Type[BaseCommand]):
        """Register a command class. Instantiates it and stores by action name."""
        instance = command_cls()
        self._commands[instance.action] = instance

    def execute(self, action: str, params: dict, context: dict) -> dict:
        """Execute a registered command by action name."""
        command = self._commands.get(action)
        if command is None:
            return {"success": False, "error": f"未知指令: {action}"}
        try:
            return command.execute(params, context)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_actions(self) -> list[str]:
        """Return all registered action names."""
        return list(self._commands.keys())
```

- [ ] **Step 4: Create package __init__.py files**

```python
# commands/__init__.py
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd E:/Inori_Code/Intrest/AIMoeMaker && python -m pytest tests/test_command_engine.py -v`
Expected: All 3 tests PASS

- [ ] **Step 6: Commit**

```bash
git add core/command_engine.py commands/
git commit -m "feat: command engine with registry and dispatch"
```

---

### Task 6: Body Command (create_base_body)

**Files:**
- Create: `AIMoeMaker/commands/body.py`
- Create: `AIMoeMaker/tests/test_body_command.py`

The first real command. Since Blender (`bpy`) won't be available in regular pytest, this command will have its logic split: parameter validation and state update (testable without bpy) and Blender mesh operations (tested via `blender --background`).

- [ ] **Step 1: Write failing tests (pure logic, no bpy)**

```python
# tests/test_body_command.py
from commands.body import CreateBaseBody, AdjustProportions, SetHeight
from core.model_state import ModelState


def test_create_base_body_updates_state():
    state = ModelState()
    cmd = CreateBaseBody()
    context = {"model_state": state, "bpy_available": False}
    result = cmd.execute({"body_type": "loli", "height": 145.0}, context)

    assert result["success"] is True
    assert state.body.body_type == "loli"
    assert state.body.height == 145.0


def test_create_base_body_defaults():
    state = ModelState()
    cmd = CreateBaseBody()
    context = {"model_state": state, "bpy_available": False}
    result = cmd.execute({}, context)

    assert result["success"] is True
    assert state.body.body_type == "default"
    assert state.body.height == 158.0


def test_set_height():
    state = ModelState()
    cmd = SetHeight()
    context = {"model_state": state, "bpy_available": False}
    result = cmd.execute({"height": 170.0}, context)

    assert result["success"] is True
    assert state.body.height == 170.0


def test_set_height_validation():
    state = ModelState()
    cmd = SetHeight()
    context = {"model_state": state, "bpy_available": False}
    result = cmd.execute({"height": -10.0}, context)

    assert result["success"] is False
    assert "范围" in result["error"]


def test_adjust_proportions():
    state = ModelState()
    cmd = AdjustProportions()
    context = {"model_state": state, "bpy_available": False}
    result = cmd.execute({"bust": 0.7, "waist": 0.3}, context)

    assert result["success"] is True
    assert state.body.bust == 0.7
    assert state.body.waist == 0.3
    assert state.body.hip == 0.5  # unchanged
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd E:/Inori_Code/Intrest/AIMoeMaker && python -m pytest tests/test_body_command.py -v`
Expected: FAIL

- [ ] **Step 3: Implement body commands**

```python
# commands/body.py
"""
Body-related commands: create base body, adjust proportions, set height.
"""
from commands.base import BaseCommand
from core.model_state import ModelState

# Body type presets: (height, head_ratio, bust, waist, hip)
BODY_PRESETS = {
    "loli": (145.0, 1.2, 0.2, 0.4, 0.3),
    "teen": (155.0, 1.0, 0.4, 0.45, 0.45),
    "default": (158.0, 1.0, 0.5, 0.5, 0.5),
    "adult": (165.0, 0.9, 0.6, 0.5, 0.55),
}


class CreateBaseBody(BaseCommand):
    action = "create_base_body"

    def execute(self, params: dict, context: dict) -> dict:
        state: ModelState = context["model_state"]
        body_type = params.get("body_type", "default")
        height = params.get("height", None)

        if body_type not in BODY_PRESETS:
            return {"success": False, "error": f"未知体型: {body_type}，可选: {list(BODY_PRESETS.keys())}"}

        preset = BODY_PRESETS[body_type]
        state.body.body_type = body_type
        state.body.height = height if height is not None else preset[0]
        state.body.head_ratio = preset[1]
        state.body.bust = preset[2]
        state.body.waist = preset[3]
        state.body.hip = preset[4]

        # Blender mesh creation (only when bpy is available)
        if context.get("bpy_available", False):
            self._create_mesh(state, context)

        return {"success": True, "message": f"已创建{body_type}体型，身高{state.body.height}cm"}

    def _create_mesh(self, state: ModelState, context: dict):
        """Create the base body mesh in Blender. Called only when bpy is available."""
        import bpy

        # Remove existing body if any
        for obj in bpy.data.objects:
            if obj.get("aimm_type") == "body":
                bpy.data.objects.remove(obj, do_unlink=True)

        # Create a basic humanoid shape using a scaled cube as placeholder
        # (In production, this would load a proper base mesh or generate one procedurally)
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, state.body.height / 200))
        body_obj = bpy.context.active_object
        body_obj.name = "AIMoeMaker_Body"
        body_obj["aimm_type"] = "body"

        # Scale to approximate body proportions
        height_m = state.body.height / 100.0
        body_obj.scale = (0.3, 0.2, height_m / 2)
        bpy.ops.object.transform_apply(scale=True)


class SetHeight(BaseCommand):
    action = "set_height"

    def execute(self, params: dict, context: dict) -> dict:
        state: ModelState = context["model_state"]
        height = params.get("height", None)

        if height is None:
            return {"success": False, "error": "缺少参数: height"}
        if not (50.0 <= height <= 300.0):
            return {"success": False, "error": f"身高{height}cm超出合理范围(50-300cm)"}

        old_height = state.body.height
        state.body.height = height

        if context.get("bpy_available", False):
            self._update_mesh(state, old_height, context)

        return {"success": True, "message": f"身高已从{old_height}cm调整为{height}cm"}

    def _update_mesh(self, state: ModelState, old_height: float, context: dict):
        import bpy
        for obj in bpy.data.objects:
            if obj.get("aimm_type") == "body":
                scale_factor = state.body.height / old_height if old_height > 0 else 1.0
                obj.scale.z *= scale_factor
                obj.location.z *= scale_factor
                break


class AdjustProportions(BaseCommand):
    action = "adjust_proportions"

    def execute(self, params: dict, context: dict) -> dict:
        state: ModelState = context["model_state"]

        for key in ("bust", "waist", "hip", "head_ratio"):
            if key in params:
                value = params[key]
                if key == "head_ratio":
                    if not (0.5 <= value <= 1.5):
                        return {"success": False, "error": f"头身比{value}超出范围(0.5-1.5)"}
                else:
                    if not (0.0 <= value <= 1.0):
                        return {"success": False, "error": f"{key}值{value}超出范围(0-1)"}
                setattr(state.body, key, value)

        return {"success": True, "message": "体型比例已调整"}


# All body commands for registration
BODY_COMMANDS = [CreateBaseBody, SetHeight, AdjustProportions]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd E:/Inori_Code/Intrest/AIMoeMaker && python -m pytest tests/test_body_command.py -v`
Expected: All 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add commands/body.py tests/test_body_command.py
git commit -m "feat: body commands (create, height, proportions) with validation"
```

---

### Task 7: AI Provider Layer (OpenAI-Compatible)

**Files:**
- Create: `AIMoeMaker/ai/__init__.py`
- Create: `AIMoeMaker/ai/provider.py`
- Create: `AIMoeMaker/ai/adapters/__init__.py`
- Create: `AIMoeMaker/ai/adapters/openai_compat.py`
- Create: `AIMoeMaker/tests/test_ai_provider.py`

Uses `urllib.request` only (no external dependencies). The OpenAI-compatible adapter covers OpenAI, most Chinese LLM APIs, and custom endpoints.

- [ ] **Step 1: Write failing tests (with mocked HTTP)**

```python
# tests/test_ai_provider.py
import json
from unittest.mock import patch, MagicMock
from ai.provider import AIProviderConfig
from ai.adapters.openai_compat import OpenAICompatAdapter


def _mock_urlopen(response_body: dict):
    """Create a mock for urllib.request.urlopen that returns the given response."""
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(response_body).encode('utf-8')
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)
    return mock_response


def test_openai_compat_chat():
    config = AIProviderConfig(
        api_key="test-key",
        endpoint="https://api.example.com/v1/chat/completions",
        model="gpt-4",
    )
    adapter = OpenAICompatAdapter(config)

    mock_ai_reply = {
        "reply": "好的，我来创建一个萝莉体型。",
        "intents": [{"type": "command", "action": "create_base_body", "params": {"body_type": "loli"}}]
    }
    mock_response = _mock_urlopen({
        "choices": [{"message": {"content": json.dumps(mock_ai_reply, ensure_ascii=False)}}]
    })

    with patch("urllib.request.urlopen", return_value=mock_response):
        result = adapter.chat(
            messages=[{"role": "user", "content": "创建一个萝莉角色"}],
            system_prompt="你是建模助手",
        )

    assert result.reply == "好的，我来创建一个萝莉体型。"
    assert len(result.intents) == 1
    assert result.intents[0].action == "create_base_body"


def test_openai_compat_network_error():
    config = AIProviderConfig(
        api_key="test-key",
        endpoint="https://api.example.com/v1/chat/completions",
        model="gpt-4",
    )
    adapter = OpenAICompatAdapter(config)

    with patch("urllib.request.urlopen", side_effect=Exception("Connection refused")):
        result = adapter.chat(
            messages=[{"role": "user", "content": "hello"}],
            system_prompt="test",
        )

    assert "连接失败" in result.reply or "错误" in result.reply
    assert len(result.intents) == 0


def test_openai_compat_malformed_response():
    config = AIProviderConfig(
        api_key="test-key",
        endpoint="https://api.example.com/v1/chat/completions",
        model="gpt-4",
    )
    adapter = OpenAICompatAdapter(config)

    # AI returns non-JSON text
    mock_response = _mock_urlopen({
        "choices": [{"message": {"content": "我不太理解你的意思，能再说一次吗？"}}]
    })

    with patch("urllib.request.urlopen", return_value=mock_response):
        result = adapter.chat(
            messages=[{"role": "user", "content": "blah"}],
            system_prompt="test",
        )

    # Should gracefully fall back to treating the whole text as reply
    assert "理解" in result.reply
    assert len(result.intents) == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd E:/Inori_Code/Intrest/AIMoeMaker && python -m pytest tests/test_ai_provider.py -v`
Expected: FAIL

- [ ] **Step 3: Implement provider.py**

```python
# ai/provider.py
"""
AI Provider base class and configuration.
"""
from dataclasses import dataclass
from typing import Optional
from prompts.intent_schema import AIResponse


@dataclass
class AIProviderConfig:
    api_key: str = ""
    endpoint: str = ""
    model: str = ""
    max_tokens: int = 2048
    temperature: float = 0.7
    timeout: int = 60  # seconds


class AIProvider:
    """Base class for AI providers."""

    def __init__(self, config: AIProviderConfig):
        self.config = config

    def chat(self, messages: list[dict], system_prompt: str) -> AIResponse:
        raise NotImplementedError

    def validate_config(self) -> Optional[str]:
        """Return error message if config is invalid, None if OK."""
        if not self.config.api_key:
            return "API Key 未设置"
        if not self.config.endpoint:
            return "API 端点未设置"
        if not self.config.model:
            return "模型名称未设置"
        return None
```

- [ ] **Step 4: Implement openai_compat.py**

```python
# ai/adapters/openai_compat.py
"""
OpenAI-compatible API adapter.
Works with: OpenAI, Azure OpenAI, Ollama (with OpenAI compat), most Chinese LLM APIs.
"""
import json
import urllib.request
import urllib.error
from ai.provider import AIProvider, AIProviderConfig
from prompts.intent_schema import AIResponse, parse_ai_response


class OpenAICompatAdapter(AIProvider):
    """Adapter for any OpenAI-compatible chat completions API."""

    def __init__(self, config: AIProviderConfig):
        super().__init__(config)

    def chat(self, messages: list[dict], system_prompt: str) -> AIResponse:
        """Send chat request and parse response."""
        # Build request body
        full_messages = [{"role": "system", "content": system_prompt}]
        full_messages.extend(messages)

        body = {
            "model": self.config.model,
            "messages": full_messages,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}",
        }

        try:
            req = urllib.request.Request(
                self.config.endpoint,
                data=json.dumps(body).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.config.timeout) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))

            # Extract content from OpenAI response format
            content = resp_data["choices"][0]["message"]["content"]
            return parse_ai_response(content)

        except urllib.error.HTTPError as e:
            error_body = ""
            try:
                error_body = e.read().decode("utf-8")
            except Exception:
                pass
            return AIResponse(
                reply=f"AI 服务返回错误 (HTTP {e.code}): {error_body[:200]}",
                raw=error_body,
            )
        except urllib.error.URLError as e:
            return AIResponse(reply=f"连接失败: {e.reason}")
        except Exception as e:
            return AIResponse(reply=f"AI 调用出错: {str(e)}")
```

- [ ] **Step 5: Create __init__.py files**

```python
# ai/__init__.py
```

```python
# ai/adapters/__init__.py
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd E:/Inori_Code/Intrest/AIMoeMaker && python -m pytest tests/test_ai_provider.py -v`
Expected: All 3 tests PASS

- [ ] **Step 7: Commit**

```bash
git add ai/ tests/test_ai_provider.py
git commit -m "feat: OpenAI-compatible AI provider with error handling"
```

---

### Task 8: Session Manager

**Files:**
- Create: `AIMoeMaker/core/session.py`
- Create: `AIMoeMaker/tests/test_session.py`

Manages conversation history, ModelState, context window compression, and project persistence.

- [ ] **Step 1: Write failing tests**

```python
# tests/test_session.py
import json
import tempfile
import os
from core.session import SessionManager
from core.model_state import ModelState


def test_add_message():
    session = SessionManager()
    session.add_message("user", "创建一个萝莉角色")
    session.add_message("assistant", "好的，我来创建。")

    assert len(session.conversation) == 2
    assert session.conversation[0]["role"] == "user"
    assert session.conversation[1]["role"] == "assistant"


def test_get_context_messages():
    session = SessionManager()
    for i in range(30):
        session.add_message("user", f"消息{i}")
        session.add_message("assistant", f"回复{i}")

    # Should return limited messages, not all 60
    messages = session.get_context_messages(max_turns=5)
    assert len(messages) == 10  # 5 turns = 10 messages (user + assistant)


def test_mark_key_decision():
    session = SessionManager()
    session.add_message("user", "我要一个银发红瞳的角色")
    session.mark_key_decision(0)

    messages = session.get_context_messages(max_turns=2)
    # Key decisions should always be included
    assert any("银发红瞳" in m["content"] for m in messages)


def test_save_and_load_project():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Save
        session = SessionManager()
        session.add_message("user", "你好")
        session.model_state.body.height = 145.0
        session.save_project(tmpdir, "test_project")

        # Load
        session2 = SessionManager()
        session2.load_project(tmpdir, "test_project")

        assert len(session2.conversation) == 1
        assert session2.model_state.body.height == 145.0


def test_model_state_summary_in_context():
    session = SessionManager()
    session.model_state.body.height = 145.0
    session.model_state.body.body_type = "loli"
    summary = session.model_state.to_summary()
    assert "145" in summary
    assert "loli" in summary
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd E:/Inori_Code/Intrest/AIMoeMaker && python -m pytest tests/test_session.py -v`
Expected: FAIL

- [ ] **Step 3: Implement SessionManager**

```python
# core/session.py
"""
Session Manager: conversation history, model state, project persistence.
"""
import json
import os
import time
from dataclasses import dataclass, field
from core.model_state import ModelState

SCHEMA_VERSION = 1


@dataclass
class Message:
    role: str
    content: str
    timestamp: float = 0.0
    is_key_decision: bool = False
    intents_executed: list[dict] = field(default_factory=list)


class SessionManager:
    def __init__(self):
        self.conversation: list[dict] = []
        self.model_state: ModelState = ModelState()
        self._key_decision_indices: set[int] = set()

    def add_message(self, role: str, content: str, intents_executed: list[dict] = None):
        """Add a message to conversation history."""
        msg = {
            "role": role,
            "content": content,
            "timestamp": time.time(),
            "is_key_decision": False,
        }
        if intents_executed:
            msg["intents_executed"] = intents_executed
        self.conversation.append(msg)

    def mark_key_decision(self, index: int):
        """Mark a message as a key decision point (preserved during context compression)."""
        if 0 <= index < len(self.conversation):
            self.conversation[index]["is_key_decision"] = True
            self._key_decision_indices.add(index)

    def get_context_messages(self, max_turns: int = 10) -> list[dict]:
        """
        Build the context window for the AI.
        Includes: key decision messages + most recent N turns.
        Returns list of {"role": ..., "content": ...} dicts.
        """
        messages = []

        # Collect key decision messages first
        key_msgs = []
        for i, msg in enumerate(self.conversation):
            if msg.get("is_key_decision", False):
                key_msgs.append(msg)

        # Collect recent messages (max_turns * 2 for user+assistant pairs)
        max_messages = max_turns * 2
        recent_start = max(0, len(self.conversation) - max_messages)
        recent_msgs = self.conversation[recent_start:]

        # Merge: key decisions first (that aren't in recent), then recent
        seen_contents = set()
        for msg in key_msgs:
            key = (msg["role"], msg["content"])
            if key not in seen_contents:
                messages.append({"role": msg["role"], "content": msg["content"]})
                seen_contents.add(key)

        for msg in recent_msgs:
            key = (msg["role"], msg["content"])
            if key not in seen_contents:
                messages.append({"role": msg["role"], "content": msg["content"]})
                seen_contents.add(key)

        return messages

    def save_project(self, base_dir: str, project_name: str):
        """Save session to a project directory."""
        project_dir = os.path.join(base_dir, project_name)
        os.makedirs(project_dir, exist_ok=True)

        # Save project metadata
        project_meta = {
            "schema_version": SCHEMA_VERSION,
            "name": project_name,
            "created": time.time(),
        }
        with open(os.path.join(project_dir, "project.json"), "w", encoding="utf-8") as f:
            json.dump(project_meta, f, ensure_ascii=False, indent=2)

        # Save session (conversation + model state)
        session_data = {
            "schema_version": SCHEMA_VERSION,
            "conversation": self.conversation,
            "model_state": self.model_state.to_dict(),
        }
        with open(os.path.join(project_dir, "session.json"), "w", encoding="utf-8") as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)

    def load_project(self, base_dir: str, project_name: str) -> bool:
        """Load session from a project directory. Returns True on success."""
        project_dir = os.path.join(base_dir, project_name)
        session_path = os.path.join(project_dir, "session.json")

        if not os.path.exists(session_path):
            return False

        with open(session_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.conversation = data.get("conversation", [])
        if "model_state" in data:
            self.model_state = ModelState.from_dict(data["model_state"])

        # Rebuild key decision index
        self._key_decision_indices.clear()
        for i, msg in enumerate(self.conversation):
            if msg.get("is_key_decision", False):
                self._key_decision_indices.add(i)

        return True

    def clear(self):
        """Reset session to initial state."""
        self.conversation.clear()
        self.model_state = ModelState()
        self._key_decision_indices.clear()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd E:/Inori_Code/Intrest/AIMoeMaker && python -m pytest tests/test_session.py -v`
Expected: All 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add core/session.py tests/test_session.py
git commit -m "feat: session manager with persistence and context compression"
```

---

### Task 9: Undo Utilities

**Files:**
- Create: `AIMoeMaker/utils/__init__.py`
- Create: `AIMoeMaker/utils/undo.py`

Thin wrappers around Blender's undo system with semantic labels. These will only be called when bpy is available.

- [ ] **Step 1: Create undo.py**

```python
# utils/undo.py
"""
Undo helpers that wrap Blender's undo system with semantic labels.
Only call these functions when bpy is available (inside Blender).
"""


def push_undo(label: str):
    """Push an undo step with a semantic label."""
    try:
        import bpy
        bpy.ops.ed.undo_push(message=f"AIMoeMaker: {label}")
    except Exception:
        pass  # Not in Blender context


def undo():
    """Undo the last operation."""
    try:
        import bpy
        bpy.ops.ed.undo()
    except Exception:
        pass


def redo():
    """Redo the last undone operation."""
    try:
        import bpy
        bpy.ops.ed.redo()
    except Exception:
        pass
```

- [ ] **Step 2: Commit**

```bash
git add utils/
git commit -m "feat: undo utility wrappers"
```

---

### Task 10: Addon Preferences (API Configuration UI)

**Files:**
- Create: `AIMoeMaker/ui/__init__.py`
- Create: `AIMoeMaker/ui/preferences.py`

Blender addon preferences panel where users configure their API key, endpoint, and model. This must be implemented as a Blender AddonPreferences class — no unit test possible without Blender, so we verify via `blender --background`.

- [ ] **Step 1: Create preferences.py**

```python
# ui/preferences.py
"""
Addon preferences: API key, endpoint URL, model name configuration.
"""
import bpy


class AIMoeMakerPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__ or "AIMoeMaker"  # __package__ resolves correctly for Extensions Platform

    api_key: bpy.props.StringProperty(
        name="API Key",
        description="AI 服务的 API Key",
        subtype='PASSWORD',
        default="",
    )

    api_endpoint: bpy.props.StringProperty(
        name="API 端点",
        description="OpenAI 兼容的 API 端点 URL",
        default="https://api.openai.com/v1/chat/completions",
    )

    model_name: bpy.props.StringProperty(
        name="模型名称",
        description="使用的 AI 模型名称",
        default="gpt-4o",
    )

    max_tokens: bpy.props.IntProperty(
        name="最大 Token 数",
        description="AI 回复的最大 token 数量",
        default=2048,
        min=256,
        max=16384,
    )

    temperature: bpy.props.FloatProperty(
        name="温度",
        description="AI 生成的随机性 (0=确定性, 1=创造性)",
        default=0.7,
        min=0.0,
        max=2.0,
    )

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
```

- [ ] **Step 2: Create ui/__init__.py**

```python
# ui/__init__.py
```

- [ ] **Step 3: Commit**

```bash
git add ui/
git commit -m "feat: addon preferences for API configuration"
```

---

### Task 11: Chat Panel UI

**Files:**
- Create: `AIMoeMaker/ui/chat_panel.py`
- Create: `AIMoeMaker/ui/operators.py`

The main user interface: a sidebar panel in the 3D viewport with chat input and message display.

- [ ] **Step 1: Create operators.py**

```python
# ui/operators.py
"""
Blender operators for AIMoeMaker interactions.
"""
import bpy
import threading
import queue
from ai.provider import AIProviderConfig
from ai.adapters.openai_compat import OpenAICompatAdapter
from core.session import SessionManager
from core.intent_router import IntentRouter
from core.command_engine import CommandEngine
from core.model_state import ModelState
from commands.body import BODY_COMMANDS
from prompts.system_prompt import build_system_prompt
from prompts.intent_schema import parse_ai_response
from utils.undo import push_undo, undo

# Global session state (persists across operator calls)
_session: SessionManager = None
_engine: CommandEngine = None
# Thread-safe queue for AI responses (avoids writing to bpy from background thread)
_response_queue: queue.Queue = queue.Queue()


def get_session() -> SessionManager:
    global _session
    if _session is None:
        _session = SessionManager()
    return _session


def get_engine() -> CommandEngine:
    global _engine
    if _engine is None:
        _engine = CommandEngine()
        for cmd_cls in BODY_COMMANDS:
            _engine.register(cmd_cls)
    return _engine


def _get_addon_name() -> str:
    return __package__ or "AIMoeMaker"


def _get_adapter(context) -> OpenAICompatAdapter:
    prefs = context.preferences.addons[_get_addon_name()].preferences
    config = AIProviderConfig(
        api_key=prefs.api_key,
        endpoint=prefs.api_endpoint,
        model=prefs.model_name,
        max_tokens=prefs.max_tokens,
        temperature=prefs.temperature,
    )
    return OpenAICompatAdapter(config)


class AIMM_OT_SendMessage(bpy.types.Operator):
    bl_idname = "aimm.send_message"
    bl_label = "发送消息"
    bl_description = "发送消息给 AI 助手"

    def execute(self, context):
        scene = context.scene
        user_input = scene.aimm_chat_input.strip()
        if not user_input:
            return {'CANCELLED'}

        session = get_session()
        engine = get_engine()

        # Add user message
        session.add_message("user", user_input)
        scene.aimm_chat_input = ""

        # Set loading state
        scene.aimm_is_loading = True

        # Run AI call in background thread
        adapter = _get_adapter(context)
        system_prompt = build_system_prompt(session.model_state.to_summary())
        context_messages = session.get_context_messages(max_turns=10)

        thread = threading.Thread(
            target=self._ai_call,
            args=(adapter, system_prompt, context_messages),
            daemon=True,
        )
        thread.start()

        # Register timer to check for completion
        bpy.app.timers.register(self._check_completion, first_interval=0.5)

        return {'FINISHED'}

    @staticmethod
    def _ai_call(adapter, system_prompt, context_messages):
        """Run in background thread. Puts result into thread-safe queue."""
        ai_response = adapter.chat(
            messages=context_messages,
            system_prompt=system_prompt,
        )
        # Put result into thread-safe queue (never touch bpy from background thread)
        _response_queue.put({
            "reply": ai_response.reply,
            "intents": [
                {
                    "type": i.intent_type,
                    "action": i.action,
                    "params": i.params,
                    "code": i.code,
                    "description": i.description,
                }
                for i in ai_response.intents
            ],
        })

    @staticmethod
    def _check_completion():
        """Timer callback on main thread. Reads from queue, executes intents."""
        try:
            pending = _response_queue.get_nowait()
        except queue.Empty:
            return 0.5  # Check again in 0.5s

        # Process response on main thread (safe to use bpy here)
        session = get_session()
        engine = get_engine()

        reply = pending["reply"]
        intents_data = pending["intents"]

        # Re-parse intents
        from prompts.intent_schema import Intent, AIResponse
        intents = [
            Intent(
                intent_type=i["type"],
                action=i["action"],
                params=i["params"],
                code=i["code"],
                description=i["description"],
            )
            for i in intents_data
        ]
        response = AIResponse(reply=reply, intents=intents)

        # Execute intents
        if response.intents:
            push_undo("AI操作")
            router = IntentRouter(
                command_handler=lambda action, params: engine.execute(
                    action, params,
                    context={"model_state": session.model_state, "bpy_available": True}
                )
            )
            results = router.execute(response)

            # Rollback on failure (per spec: whole-response rollback)
            if any(not r.get("success", False) for r in results):
                undo()  # Revert to pre-execution snapshot

            session.add_message("assistant", reply, intents_executed=results)
        else:
            session.add_message("assistant", reply)

        # Clear loading state
        bpy.context.scene.aimm_is_loading = False

        # Force UI redraw
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

        return None  # Stop timer


class AIMM_OT_Undo(bpy.types.Operator):
    bl_idname = "aimm.undo"
    bl_label = "撤销"
    bl_description = "撤销上一步 AI 操作"

    def execute(self, context):
        from utils.undo import undo
        undo()
        return {'FINISHED'}


class AIMM_OT_ClearChat(bpy.types.Operator):
    bl_idname = "aimm.clear_chat"
    bl_label = "清空对话"
    bl_description = "清空对话历史并重置"

    def execute(self, context):
        session = get_session()
        session.clear()
        return {'FINISHED'}


OPERATOR_CLASSES = [AIMM_OT_SendMessage, AIMM_OT_Undo, AIMM_OT_ClearChat]
```

- [ ] **Step 2: Create chat_panel.py**

```python
# ui/chat_panel.py
"""
Main chat panel in the 3D viewport sidebar.
"""
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

        # Chat history
        chat_box = layout.box()
        chat_box.label(text="对话", icon='TEXT')

        if not session.conversation:
            chat_box.label(text="描述你想创建的角色吧！", icon='INFO')
        else:
            # Show last 10 messages to avoid UI overflow
            messages = session.conversation[-10:]
            for msg in messages:
                row = chat_box.row()
                if msg["role"] == "user":
                    row.label(text=f"你: {msg['content'][:80]}", icon='USER')
                else:
                    row.label(text=f"AI: {msg['content'][:80]}", icon='LIGHT')

        # Loading indicator
        if scene.aimm_is_loading:
            layout.label(text="AI 思考中...", icon='TIME')

        # Input area
        input_box = layout.box()
        input_box.prop(scene, "aimm_chat_input", text="")
        row = input_box.row(align=True)
        row.operator("aimm.send_message", text="发送", icon='PLAY')
        row.operator("aimm.undo", text="撤销", icon='LOOP_BACK')
        row.operator("aimm.clear_chat", text="清空", icon='TRASH')

        # Model state summary
        state_box = layout.box()
        state_box.label(text="当前模型状态", icon='OBJECT_DATA')
        for line in session.model_state.to_summary().split("\n"):
            state_box.label(text=line)


PANEL_CLASSES = [AIMM_PT_ChatPanel]
```

- [ ] **Step 3: Commit**

```bash
git add ui/chat_panel.py ui/operators.py
git commit -m "feat: chat panel UI with async AI communication"
```

---

### Task 12: Wire Everything Together in __init__.py

**Files:**
- Modify: `AIMoeMaker/__init__.py`

Connect all modules: register Blender classes, properties, and preferences.

- [ ] **Step 1: Update __init__.py**

```python
# __init__.py
bl_info = {
    "name": "AIMoeMaker",
    "author": "AIMoeMaker Team",
    "version": (0, 1, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > AIMoeMaker",
    "description": "AI驱动的MMD建模助手，通过自然语言对话创建MMD模型",
    "category": "3D View",
}

import bpy
from ui.preferences import PREFERENCE_CLASSES
from ui.operators import OPERATOR_CLASSES
from ui.chat_panel import PANEL_CLASSES

ALL_CLASSES = PREFERENCE_CLASSES + OPERATOR_CLASSES + PANEL_CLASSES


def register():
    for cls in ALL_CLASSES:
        bpy.utils.register_class(cls)

    # Scene properties for chat
    bpy.types.Scene.aimm_chat_input = bpy.props.StringProperty(
        name="消息",
        description="输入消息给 AI 助手",
        default="",
    )
    bpy.types.Scene.aimm_is_loading = bpy.props.BoolProperty(
        name="加载中",
        default=False,
    )


def unregister():
    del bpy.types.Scene.aimm_is_loading
    del bpy.types.Scene.aimm_chat_input

    for cls in reversed(ALL_CLASSES):
        bpy.utils.unregister_class(cls)
```

- [ ] **Step 2: Verify addon loads in Blender with all components**

Run: `blender --background --python-expr "import bpy; bpy.ops.preferences.addon_enable(module='AIMoeMaker'); print('Classes registered:', len([c for c in dir(bpy.types) if 'AIMM' in c])); print('ADDON LOADED OK')"`

Expected: `Classes registered: 5` (or similar), `ADDON LOADED OK`

- [ ] **Step 3: Commit**

```bash
git add __init__.py
git commit -m "feat: wire all modules together in addon registration"
```

---

### Task 13: End-to-End Integration Test

**Files:**
- Create: `AIMoeMaker/tests/test_integration.py`
- Create: `AIMoeMaker/tests/run_tests.py`

Verify the complete flow works: user message → AI response (mocked) → intent routing → command execution → model state update.

- [ ] **Step 1: Write integration test (no bpy required)**

```python
# tests/test_integration.py
"""
End-to-end integration test: user message → AI response → intent → command → state update.
Mocks the AI provider, tests everything else for real.
"""
import json
from unittest.mock import patch, MagicMock
from core.session import SessionManager
from core.intent_router import IntentRouter
from core.command_engine import CommandEngine
from commands.body import BODY_COMMANDS
from ai.adapters.openai_compat import OpenAICompatAdapter
from ai.provider import AIProviderConfig
from prompts.system_prompt import build_system_prompt
from prompts.intent_schema import parse_ai_response


def _mock_ai_response(reply: str, intents: list[dict]):
    """Create a mock urlopen that returns a structured AI response."""
    ai_reply = {"reply": reply, "intents": intents}
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps({
        "choices": [{"message": {"content": json.dumps(ai_reply, ensure_ascii=False)}}]
    }).encode("utf-8")
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


def test_full_flow_create_body():
    """Simulate: user says '创建一个萝莉角色' → AI returns create_base_body intent → body state updated."""
    # Setup
    session = SessionManager()
    engine = CommandEngine()
    for cmd_cls in BODY_COMMANDS:
        engine.register(cmd_cls)

    # User input
    user_input = "创建一个萝莉角色，身高145cm"
    session.add_message("user", user_input)

    # Mock AI response
    mock_response = _mock_ai_response(
        reply="好的，我来创建一个145cm的萝莉体型角色。",
        intents=[{
            "type": "command",
            "action": "create_base_body",
            "params": {"body_type": "loli", "height": 145.0}
        }]
    )

    config = AIProviderConfig(api_key="test", endpoint="https://test.com/v1/chat/completions", model="test")
    adapter = OpenAICompatAdapter(config)

    with patch("urllib.request.urlopen", return_value=mock_response):
        system_prompt = build_system_prompt(session.model_state.to_summary())
        ai_response = adapter.chat(
            messages=session.get_context_messages(),
            system_prompt=system_prompt,
        )

    # Route intents
    router = IntentRouter(
        command_handler=lambda action, params: engine.execute(
            action, params,
            context={"model_state": session.model_state, "bpy_available": False}
        )
    )
    results = router.execute(ai_response)

    # Verify
    assert results[0]["success"] is True
    assert session.model_state.body.body_type == "loli"
    assert session.model_state.body.height == 145.0

    # Add assistant message
    session.add_message("assistant", ai_response.reply, intents_executed=results)
    assert len(session.conversation) == 2


def test_full_flow_multi_intent():
    """Simulate: user gives multiple instructions → AI returns multiple intents."""
    session = SessionManager()
    engine = CommandEngine()
    for cmd_cls in BODY_COMMANDS:
        engine.register(cmd_cls)

    mock_response = _mock_ai_response(
        reply="好的，我来创建角色并调整比例。",
        intents=[
            {"type": "command", "action": "create_base_body", "params": {"body_type": "adult", "height": 170.0}},
            {"type": "command", "action": "adjust_proportions", "params": {"bust": 0.7, "waist": 0.4}},
        ]
    )

    config = AIProviderConfig(api_key="test", endpoint="https://test.com/v1/chat/completions", model="test")
    adapter = OpenAICompatAdapter(config)

    with patch("urllib.request.urlopen", return_value=mock_response):
        ai_response = adapter.chat(messages=[], system_prompt="test")

    router = IntentRouter(
        command_handler=lambda action, params: engine.execute(
            action, params,
            context={"model_state": session.model_state, "bpy_available": False}
        )
    )
    results = router.execute(ai_response)

    assert len(results) == 2
    assert all(r["success"] for r in results)
    assert session.model_state.body.height == 170.0
    assert session.model_state.body.bust == 0.7


def test_full_flow_ai_asks_question():
    """When AI has no intents (asking a question), no commands should execute."""
    mock_response = _mock_ai_response(
        reply="你想要什么风格的角色呢？比如萝莉、少女、还是成人体型？",
        intents=[]
    )

    config = AIProviderConfig(api_key="test", endpoint="https://test.com/v1/chat/completions", model="test")
    adapter = OpenAICompatAdapter(config)

    with patch("urllib.request.urlopen", return_value=mock_response):
        ai_response = adapter.chat(messages=[], system_prompt="test")

    router = IntentRouter(
        command_handler=lambda action, params: {"success": True}
    )
    results = router.execute(ai_response)

    assert results == []
    assert "风格" in ai_response.reply
```

- [ ] **Step 2: Create run_tests.py for Blender headless tests (future use)**

```python
# tests/run_tests.py
"""
Run tests that require Blender via: blender --background --python tests/run_tests.py
For now, most tests run fine with regular pytest.
"""
import subprocess
import sys
import os

def main():
    addon_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    result = subprocess.run(
        [sys.executable, "-m", "pytest", os.path.join(addon_dir, "tests"), "-v"],
        cwd=addon_dir,
    )
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Run all tests**

Run: `cd E:/Inori_Code/Intrest/AIMoeMaker && python -m pytest tests/ -v`
Expected: All tests PASS (16+ tests across all test files)

- [ ] **Step 4: Commit**

```bash
git add tests/
git commit -m "feat: end-to-end integration tests for full conversation flow"
```

---

### Task 14: Final Verification + README

**Files:**
- Create: `AIMoeMaker/.gitignore`

- [ ] **Step 1: Create .gitignore**

```
__pycache__/
*.pyc
.pytest_cache/
user_data/
*.blend1
```

- [ ] **Step 2: Run full test suite**

Run: `cd E:/Inori_Code/Intrest/AIMoeMaker && python -m pytest tests/ -v --tb=short`
Expected: All tests PASS

- [ ] **Step 3: Verify addon loads in Blender**

Run: `blender --background --python-expr "import bpy; bpy.ops.preferences.addon_enable(module='AIMoeMaker'); print('OK')"`
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add .gitignore
git commit -m "chore: add gitignore for Python cache and user data"
```

---

## Summary

After completing Phase 1, you will have:
- A working Blender 4.2 addon that loads and shows a chat panel in the sidebar
- AI integration via any OpenAI-compatible API
- Intent parsing and routing infrastructure
- Body creation commands (create, height, proportions)
- Session management with persistence and context compression
- Undo support
- 16+ passing tests covering all non-UI logic

**Next:** Phase 2 will add the remaining MMD commands (hair, face, clothing, skeleton, physics, morph), the PMX Export Pipeline, and the Quick Panel UI.
