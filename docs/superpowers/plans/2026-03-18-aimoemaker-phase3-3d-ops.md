# AIMoeMaker Phase 3: 3D Operations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement actual Blender 3D geometry operations so commands produce visible results in the viewport. After this, a user can go from natural language description to a visible 3D character with skeleton in Blender.

**Architecture:** A new `blender_ops/` module contains all Blender-specific geometry operations, separated from command logic. Commands call into these modules only when `bpy_available=True`. This keeps commands testable without Blender while the 3D ops can be tested via `blender --background`.

**Approach:** Since generating production-quality humanoid meshes procedurally is extremely complex, we use a pragmatic approach:
- Body: parametric mesh using scaled primitives + subdivision (functional, not production quality)
- Hair: curve-based procedural hair strips
- Skeleton: precise MMD bone hierarchy (well-defined spec, high quality)
- Physics: MMD rigid body + joint setup (well-defined spec)
- Morph: shape key framework (standard MMD expressions)

---

## File Structure (new)

```
AIMoeMaker/
  blender_ops/
    __init__.py
    body_ops.py         ← Parametric body mesh generation
    hair_ops.py         ← Curve-based hair generation
    skeleton_ops.py     ← MMD standard armature creation
    physics_ops.py      ← Rigid body + joint setup
    morph_ops.py        ← Shape key creation
    utils.py            ← Shared helpers (find object by aimm_type, etc.)
```

---

### Task 1: Blender Ops Utilities

Create shared helpers used by all 3D operations.

**Files:** Create `blender_ops/__init__.py`, `blender_ops/utils.py`

### Task 2: Body Mesh Generation

Create a parametric humanoid body using Blender primitives.

**Files:** Create `blender_ops/body_ops.py`, Modify `commands/body.py`

### Task 3: Hair Generation

Create procedural hair using Blender curves.

**Files:** Create `blender_ops/hair_ops.py`, Modify `commands/hair.py`

### Task 4: MMD Skeleton

Create the full MMD standard armature with correct bone positions.

**Files:** Create `blender_ops/skeleton_ops.py`, Modify `commands/skeleton.py`

### Task 5: Physics Setup

Create MMD rigid bodies and joints for hair/cloth physics.

**Files:** Create `blender_ops/physics_ops.py`, Modify `commands/physics.py`

### Task 6: Morph/Expression Setup

Create shape keys for standard MMD expressions.

**Files:** Create `blender_ops/morph_ops.py`, Modify `commands/morph.py`
