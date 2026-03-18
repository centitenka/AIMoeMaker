# AIMoeMaker Phase 2b: Quick Panel UI + Code Sandbox

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add Quick Panel mode (sliders/dropdowns for all model properties) and Code Sandbox (safe execution of AI-generated Python code). After this, the plugin's v1 feature set is complete.

**Spec:** `docs/superpowers/specs/2026-03-18-aimoemaker-design.md`

---

## Task 1: Quick Panel UI

Create a Blender panel with collapsible sections for each command category. Properties link to CommandEngine calls with debounce.

**Files:**
- Create: `ui/quick_panel.py`
- Modify: `ui/chat_panel.py` — add mode toggle buttons
- Modify: `__init__.py` — register new panel and properties

## Task 2: Code Sandbox

Implement the sandbox for AI-generated code with AST pre-checking, bpy whitelist, restricted builtins, and timeout.

**Files:**
- Create: `core/code_sandbox.py`
- Create: `tests/test_code_sandbox.py`
- Modify: `ui/operators.py` — wire sandbox into IntentRouter as code_handler

## Task 3: Integration + Final Wiring

Wire Quick Panel and Code Sandbox into the main addon, run full tests.
