# AIMoeMaker Phase 2a: All MMD Commands Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement all remaining MMD command modules (hair, face, clothing, accessory, skeleton, physics, morph, export) so the AI can drive the full character creation workflow through natural language.

**Architecture:** Each command module follows the same pattern established in Phase 1: a Python file in `commands/` with classes inheriting `BaseCommand`, updating `ModelState`, and conditionally calling `bpy` operations when available. All commands are testable without Blender via `bpy_available=False` context.

**Tech Stack:** Python 3.11+, Blender 4.2+ API (`bpy`, `bmesh`, `mathutils`), existing `CommandEngine` + `ModelState` from Phase 1.

**Spec:** `docs/superpowers/specs/2026-03-18-aimoemaker-design.md`

**Depends on:** Phase 1 complete (all 34 tests passing).

---

## File Structure (new files only)

```
AIMoeMaker/
  commands/
    hair.py               ← add_hair, modify_hair_style, set_hair_color
    face.py               ← set_eye_shape, set_eye_color, adjust_face_shape
    clothing.py           ← add_clothing, modify_clothing, set_fabric_material
    accessory.py          ← add_accessory, remove_accessory
    skeleton.py           ← setup_skeleton, auto_weight_paint
    physics.py            ← setup_hair_physics, setup_cloth_physics
    morph.py              ← create_morph, add_expression_set
    export.py             ← export_pmx, validate_pmx
  tests/
    test_hair_command.py
    test_face_command.py
    test_clothing_command.py
    test_accessory_command.py
    test_skeleton_command.py
    test_physics_command.py
    test_morph_command.py
    test_export_command.py
```

Also modified:
- `core/model_state.py` — ensure all state fields used by new commands exist
- `prompts/system_prompt.py` — add all new commands to the AI's available command list
- `ui/operators.py` — register all new commands in `get_engine()`

---

### Task 1: Hair Commands

**Files:**
- Create: `commands/hair.py`
- Create: `tests/test_hair_command.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_hair_command.py
from commands.hair import AddHair, ModifyHairStyle, SetHairColor
from core.model_state import ModelState, HairState


def test_add_hair():
    state = ModelState()
    cmd = AddHair()
    result = cmd.execute({"style": "twintail", "colors": ["#FFB6C1", "#FF69B4"], "length": 0.8}, {"model_state": state, "bpy_available": False})
    assert result["success"] is True
    assert state.hair is not None
    assert state.hair.style == "twintail"
    assert state.hair.colors == ["#FFB6C1", "#FF69B4"]
    assert state.hair.length == 0.8


def test_add_hair_defaults():
    state = ModelState()
    cmd = AddHair()
    result = cmd.execute({}, {"model_state": state, "bpy_available": False})
    assert result["success"] is True
    assert state.hair.style == "short"
    assert state.hair.colors == ["#000000"]


def test_modify_hair_style():
    state = ModelState()
    state.hair = HairState(style="short")
    cmd = ModifyHairStyle()
    result = cmd.execute({"style": "ponytail"}, {"model_state": state, "bpy_available": False})
    assert result["success"] is True
    assert state.hair.style == "ponytail"


def test_modify_hair_no_hair():
    state = ModelState()
    cmd = ModifyHairStyle()
    result = cmd.execute({"style": "ponytail"}, {"model_state": state, "bpy_available": False})
    assert result["success"] is False


def test_set_hair_color():
    state = ModelState()
    state.hair = HairState()
    cmd = SetHairColor()
    result = cmd.execute({"colors": ["#FF0000"], "gradient": True}, {"model_state": state, "bpy_available": False})
    assert result["success"] is True
    assert state.hair.colors == ["#FF0000"]
    assert state.hair.gradient is True
```

- [ ] **Step 2: Run tests, verify fail**

Run: `cd E:/Inori_Code/Intrest/AIMoeMaker && python -m pytest tests/test_hair_command.py -v`

- [ ] **Step 3: Implement hair commands**

```python
# commands/hair.py
from commands.base import BaseCommand
from core.model_state import ModelState, HairState

HAIR_STYLES = ["short", "long", "twintail", "ponytail", "bob", "hime_cut", "drill", "braid", "odango", "ahoge"]


class AddHair(BaseCommand):
    action = "add_hair"

    def execute(self, params: dict, context: dict) -> dict:
        state: ModelState = context["model_state"]
        style = params.get("style", "short")
        colors = params.get("colors", ["#000000"])
        length = params.get("length", 0.5)
        gradient = params.get("gradient", False)

        state.hair = HairState(
            style=style,
            colors=colors if isinstance(colors, list) else [colors],
            length=max(0.0, min(1.0, length)),
            gradient=gradient,
            physics_enabled=True,
        )

        if context.get("bpy_available", False):
            self._create_hair_mesh(state, context)

        return {"success": True, "message": f"已添加{style}发型"}

    def _create_hair_mesh(self, state, context):
        import bpy
        # Remove existing hair
        for obj in bpy.data.objects:
            if obj.get("aimm_type") == "hair":
                bpy.data.objects.remove(obj, do_unlink=True)
        # Placeholder: create simple hair mesh
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.15, location=(0, 0, state.body.height / 100))
        hair_obj = bpy.context.active_object
        hair_obj.name = "AIMoeMaker_Hair"
        hair_obj["aimm_type"] = "hair"


class ModifyHairStyle(BaseCommand):
    action = "modify_hair_style"

    def execute(self, params: dict, context: dict) -> dict:
        state: ModelState = context["model_state"]
        if state.hair is None:
            return {"success": False, "error": "还没有添加头发，请先使用 add_hair"}

        if "style" in params:
            state.hair.style = params["style"]
        if "length" in params:
            state.hair.length = max(0.0, min(1.0, params["length"]))

        return {"success": True, "message": f"发型已修改为{state.hair.style}"}


class SetHairColor(BaseCommand):
    action = "set_hair_color"

    def execute(self, params: dict, context: dict) -> dict:
        state: ModelState = context["model_state"]
        if state.hair is None:
            return {"success": False, "error": "还没有添加头发，请先使用 add_hair"}

        if "colors" in params:
            colors = params["colors"]
            state.hair.colors = colors if isinstance(colors, list) else [colors]
        if "gradient" in params:
            state.hair.gradient = params["gradient"]

        return {"success": True, "message": "头发颜色已更新"}


HAIR_COMMANDS = [AddHair, ModifyHairStyle, SetHairColor]
```

- [ ] **Step 4: Run tests, verify pass**

Run: `cd E:/Inori_Code/Intrest/AIMoeMaker && python -m pytest tests/test_hair_command.py -v`
Expected: All 5 PASS

- [ ] **Step 5: Commit**

```bash
git add commands/hair.py tests/test_hair_command.py
git commit -m "feat: hair commands (add, modify style, set color)"
```

---

### Task 2: Face Commands

**Files:**
- Create: `commands/face.py`
- Create: `tests/test_face_command.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_face_command.py
from commands.face import SetEyeShape, SetEyeColor, AdjustFaceShape
from core.model_state import ModelState, FaceState


def test_set_eye_shape():
    state = ModelState()
    state.face = FaceState()
    cmd = SetEyeShape()
    result = cmd.execute({"shape": "cat"}, {"model_state": state, "bpy_available": False})
    assert result["success"] is True
    assert state.face.eye_shape == "cat"


def test_set_eye_shape_creates_face():
    state = ModelState()
    cmd = SetEyeShape()
    result = cmd.execute({"shape": "round"}, {"model_state": state, "bpy_available": False})
    assert result["success"] is True
    assert state.face is not None
    assert state.face.eye_shape == "round"


def test_set_eye_color():
    state = ModelState()
    state.face = FaceState()
    cmd = SetEyeColor()
    result = cmd.execute({"color": "#FF0000"}, {"model_state": state, "bpy_available": False})
    assert result["success"] is True
    assert state.face.eye_color == "#FF0000"


def test_adjust_face_shape():
    state = ModelState()
    state.face = FaceState()
    cmd = AdjustFaceShape()
    result = cmd.execute({"shape": "heart"}, {"model_state": state, "bpy_available": False})
    assert result["success"] is True
    assert state.face.face_shape == "heart"
```

- [ ] **Step 2: Implement face commands**

```python
# commands/face.py
from commands.base import BaseCommand
from core.model_state import ModelState, FaceState

EYE_SHAPES = ["round", "almond", "cat", "droopy", "tsurime", "tareme"]
FACE_SHAPES = ["oval", "round", "heart", "square", "diamond"]


class SetEyeShape(BaseCommand):
    action = "set_eye_shape"

    def execute(self, params: dict, context: dict) -> dict:
        state: ModelState = context["model_state"]
        if state.face is None:
            state.face = FaceState()
        shape = params.get("shape", "round")
        state.face.eye_shape = shape
        return {"success": True, "message": f"眼型已设置为{shape}"}


class SetEyeColor(BaseCommand):
    action = "set_eye_color"

    def execute(self, params: dict, context: dict) -> dict:
        state: ModelState = context["model_state"]
        if state.face is None:
            state.face = FaceState()
        color = params.get("color", "#663300")
        state.face.eye_color = color
        return {"success": True, "message": f"瞳色已设置为{color}"}


class AdjustFaceShape(BaseCommand):
    action = "adjust_face_shape"

    def execute(self, params: dict, context: dict) -> dict:
        state: ModelState = context["model_state"]
        if state.face is None:
            state.face = FaceState()
        shape = params.get("shape", "oval")
        state.face.face_shape = shape
        return {"success": True, "message": f"脸型已调整为{shape}"}


FACE_COMMANDS = [SetEyeShape, SetEyeColor, AdjustFaceShape]
```

- [ ] **Step 3: Run tests, verify pass**

- [ ] **Step 4: Commit**

```bash
git add commands/face.py tests/test_face_command.py
git commit -m "feat: face commands (eye shape, eye color, face shape)"
```

---

### Task 3: Clothing Commands

**Files:**
- Create: `commands/clothing.py`
- Create: `tests/test_clothing_command.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_clothing_command.py
from commands.clothing import AddClothing, ModifyClothing, SetFabricMaterial
from core.model_state import ModelState, ClothingItem


def test_add_clothing():
    state = ModelState()
    cmd = AddClothing()
    result = cmd.execute({"type": "gothic_dress", "color": "#000000"}, {"model_state": state, "bpy_available": False})
    assert result["success"] is True
    assert len(state.clothing) == 1
    assert state.clothing[0].clothing_type == "gothic_dress"


def test_add_multiple_clothing():
    state = ModelState()
    cmd = AddClothing()
    cmd.execute({"type": "shirt"}, {"model_state": state, "bpy_available": False})
    cmd.execute({"type": "skirt"}, {"model_state": state, "bpy_available": False})
    assert len(state.clothing) == 2


def test_modify_clothing():
    state = ModelState()
    state.clothing.append(ClothingItem(clothing_type="dress", color="#FFFFFF"))
    cmd = ModifyClothing()
    result = cmd.execute({"index": 0, "color": "#000000"}, {"model_state": state, "bpy_available": False})
    assert result["success"] is True
    assert state.clothing[0].color == "#000000"


def test_modify_clothing_invalid_index():
    state = ModelState()
    cmd = ModifyClothing()
    result = cmd.execute({"index": 0, "color": "#000000"}, {"model_state": state, "bpy_available": False})
    assert result["success"] is False


def test_set_fabric_material():
    state = ModelState()
    state.clothing.append(ClothingItem(clothing_type="dress"))
    cmd = SetFabricMaterial()
    result = cmd.execute({"index": 0, "material": "silk", "physics_enabled": True}, {"model_state": state, "bpy_available": False})
    assert result["success"] is True
    assert state.clothing[0].material == "silk"
    assert state.clothing[0].physics_enabled is True
```

- [ ] **Step 2: Implement clothing commands**

```python
# commands/clothing.py
from commands.base import BaseCommand
from core.model_state import ModelState, ClothingItem


class AddClothing(BaseCommand):
    action = "add_clothing"

    def execute(self, params: dict, context: dict) -> dict:
        state: ModelState = context["model_state"]
        clothing_type = params.get("type", "generic")
        color = params.get("color", "#FFFFFF")
        material = params.get("material", "")
        physics = params.get("physics_enabled", False)

        item = ClothingItem(clothing_type=clothing_type, color=color, material=material, physics_enabled=physics)
        state.clothing.append(item)

        return {"success": True, "message": f"已添加服装: {clothing_type}"}


class ModifyClothing(BaseCommand):
    action = "modify_clothing"

    def execute(self, params: dict, context: dict) -> dict:
        state: ModelState = context["model_state"]
        index = params.get("index", 0)

        if index < 0 or index >= len(state.clothing):
            return {"success": False, "error": f"服装索引{index}无效，当前共{len(state.clothing)}件服装"}

        item = state.clothing[index]
        if "color" in params:
            item.color = params["color"]
        if "type" in params:
            item.clothing_type = params["type"]
        if "material" in params:
            item.material = params["material"]
        if "physics_enabled" in params:
            item.physics_enabled = params["physics_enabled"]

        return {"success": True, "message": f"服装已修改"}


class SetFabricMaterial(BaseCommand):
    action = "set_fabric_material"

    def execute(self, params: dict, context: dict) -> dict:
        state: ModelState = context["model_state"]
        index = params.get("index", 0)

        if index < 0 or index >= len(state.clothing):
            return {"success": False, "error": f"服装索引{index}无效"}

        item = state.clothing[index]
        if "material" in params:
            item.material = params["material"]
        if "physics_enabled" in params:
            item.physics_enabled = params["physics_enabled"]

        return {"success": True, "message": f"面料材质已设置为{item.material}"}


CLOTHING_COMMANDS = [AddClothing, ModifyClothing, SetFabricMaterial]
```

- [ ] **Step 3: Run tests, verify pass**

- [ ] **Step 4: Commit**

```bash
git add commands/clothing.py tests/test_clothing_command.py
git commit -m "feat: clothing commands (add, modify, set fabric material)"
```

---

### Task 4: Accessory Commands

**Files:**
- Create: `commands/accessory.py`
- Create: `tests/test_accessory_command.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_accessory_command.py
from commands.accessory import AddAccessory, RemoveAccessory
from core.model_state import ModelState, AccessoryItem


def test_add_accessory():
    state = ModelState()
    cmd = AddAccessory()
    result = cmd.execute({"type": "cat_ears", "position": [0, 0, 1.6]}, {"model_state": state, "bpy_available": False})
    assert result["success"] is True
    assert len(state.accessories) == 1
    assert state.accessories[0].accessory_type == "cat_ears"


def test_remove_accessory():
    state = ModelState()
    state.accessories.append(AccessoryItem(accessory_type="ribbon"))
    state.accessories.append(AccessoryItem(accessory_type="glasses"))
    cmd = RemoveAccessory()
    result = cmd.execute({"index": 0}, {"model_state": state, "bpy_available": False})
    assert result["success"] is True
    assert len(state.accessories) == 1
    assert state.accessories[0].accessory_type == "glasses"


def test_remove_accessory_by_type():
    state = ModelState()
    state.accessories.append(AccessoryItem(accessory_type="ribbon"))
    cmd = RemoveAccessory()
    result = cmd.execute({"type": "ribbon"}, {"model_state": state, "bpy_available": False})
    assert result["success"] is True
    assert len(state.accessories) == 0


def test_remove_accessory_not_found():
    state = ModelState()
    cmd = RemoveAccessory()
    result = cmd.execute({"type": "nonexistent"}, {"model_state": state, "bpy_available": False})
    assert result["success"] is False
```

- [ ] **Step 2: Implement accessory commands**

```python
# commands/accessory.py
from commands.base import BaseCommand
from core.model_state import ModelState, AccessoryItem


class AddAccessory(BaseCommand):
    action = "add_accessory"

    def execute(self, params: dict, context: dict) -> dict:
        state: ModelState = context["model_state"]
        acc_type = params.get("type", "generic")
        position = params.get("position", [0.0, 0.0, 0.0])
        scale = params.get("scale", 1.0)

        item = AccessoryItem(accessory_type=acc_type, position=position, scale=scale)
        state.accessories.append(item)

        return {"success": True, "message": f"已添加配饰: {acc_type}"}


class RemoveAccessory(BaseCommand):
    action = "remove_accessory"

    def execute(self, params: dict, context: dict) -> dict:
        state: ModelState = context["model_state"]

        if "index" in params:
            index = params["index"]
            if 0 <= index < len(state.accessories):
                removed = state.accessories.pop(index)
                return {"success": True, "message": f"已移除配饰: {removed.accessory_type}"}
            return {"success": False, "error": f"配饰索引{index}无效"}

        if "type" in params:
            acc_type = params["type"]
            for i, acc in enumerate(state.accessories):
                if acc.accessory_type == acc_type:
                    state.accessories.pop(i)
                    return {"success": True, "message": f"已移除配饰: {acc_type}"}
            return {"success": False, "error": f"未找到类型为{acc_type}的配饰"}

        return {"success": False, "error": "请指定要移除的配饰索引(index)或类型(type)"}


ACCESSORY_COMMANDS = [AddAccessory, RemoveAccessory]
```

- [ ] **Step 3: Run tests, verify pass**

- [ ] **Step 4: Commit**

```bash
git add commands/accessory.py tests/test_accessory_command.py
git commit -m "feat: accessory commands (add, remove by index/type)"
```

---

### Task 5: Skeleton + Physics + Morph + Export Commands

**Files:**
- Create: `commands/skeleton.py`, `commands/physics.py`, `commands/morph.py`, `commands/export.py`
- Create: `tests/test_skeleton_command.py`, `tests/test_physics_command.py`, `tests/test_morph_command.py`, `tests/test_export_command.py`

These commands are simpler in Phase 2a (state tracking + validation only). Full Blender integration comes in Phase 2b.

- [ ] **Step 1: Write all test files**

```python
# tests/test_skeleton_command.py
from commands.skeleton import SetupSkeleton, AutoWeightPaint
from core.model_state import ModelState


def test_setup_skeleton():
    state = ModelState()
    cmd = SetupSkeleton()
    result = cmd.execute({}, {"model_state": state, "bpy_available": False})
    assert result["success"] is True
    assert state.skeleton.is_configured is True
    assert state.skeleton.ik_setup is True


def test_auto_weight_paint():
    state = ModelState()
    state.skeleton.is_configured = True
    cmd = AutoWeightPaint()
    result = cmd.execute({}, {"model_state": state, "bpy_available": False})
    assert result["success"] is True


def test_auto_weight_paint_no_skeleton():
    state = ModelState()
    cmd = AutoWeightPaint()
    result = cmd.execute({}, {"model_state": state, "bpy_available": False})
    assert result["success"] is False
```

```python
# tests/test_physics_command.py
from commands.physics import SetupHairPhysics, SetupClothPhysics
from core.model_state import ModelState, HairState


def test_setup_hair_physics():
    state = ModelState()
    state.hair = HairState()
    cmd = SetupHairPhysics()
    result = cmd.execute({"stiffness": 0.5, "damping": 0.3}, {"model_state": state, "bpy_available": False})
    assert result["success"] is True
    assert state.physics.rigid_body_count > 0


def test_setup_hair_physics_no_hair():
    state = ModelState()
    cmd = SetupHairPhysics()
    result = cmd.execute({}, {"model_state": state, "bpy_available": False})
    assert result["success"] is False


def test_setup_cloth_physics():
    state = ModelState()
    from core.model_state import ClothingItem
    state.clothing.append(ClothingItem(clothing_type="skirt"))
    cmd = SetupClothPhysics()
    result = cmd.execute({"index": 0}, {"model_state": state, "bpy_available": False})
    assert result["success"] is True
    assert state.clothing[0].physics_enabled is True
```

```python
# tests/test_morph_command.py
from commands.morph import CreateMorph, AddExpressionSet
from core.model_state import ModelState


def test_create_morph():
    state = ModelState()
    cmd = CreateMorph()
    result = cmd.execute({"name": "smile", "category": "mouth"}, {"model_state": state, "bpy_available": False})
    assert result["success"] is True
    assert "smile" in state.morphs.expressions


def test_add_expression_set():
    state = ModelState()
    cmd = AddExpressionSet()
    result = cmd.execute({"preset": "standard"}, {"model_state": state, "bpy_available": False})
    assert result["success"] is True
    assert len(state.morphs.expressions) > 0
    assert "まばたき" in state.morphs.expressions


def test_add_expression_set_no_duplicates():
    state = ModelState()
    cmd = AddExpressionSet()
    cmd.execute({"preset": "standard"}, {"model_state": state, "bpy_available": False})
    count = len(state.morphs.expressions)
    cmd.execute({"preset": "standard"}, {"model_state": state, "bpy_available": False})
    assert len(state.morphs.expressions) == count
```

```python
# tests/test_export_command.py
from commands.export import ValidatePmx, ExportPmx
from core.model_state import ModelState


def test_validate_pmx_incomplete():
    state = ModelState()
    cmd = ValidatePmx()
    result = cmd.execute({}, {"model_state": state, "bpy_available": False})
    assert result["success"] is True
    assert len(result.get("warnings", [])) > 0


def test_validate_pmx_complete():
    state = ModelState()
    state.skeleton.is_configured = True
    state.skeleton.ik_setup = True
    state.morphs.expressions = ["まばたき", "あ"]
    cmd = ValidatePmx()
    result = cmd.execute({}, {"model_state": state, "bpy_available": False})
    assert result["success"] is True


def test_export_pmx_no_bpy():
    state = ModelState()
    cmd = ExportPmx()
    result = cmd.execute({"path": "/tmp/test.pmx"}, {"model_state": state, "bpy_available": False})
    assert result["success"] is False
    assert "Blender" in result["error"]
```

- [ ] **Step 2: Implement all four command files**

```python
# commands/skeleton.py
from commands.base import BaseCommand
from core.model_state import ModelState

MMD_STANDARD_BONES = [
    "全ての親", "センター", "グルーブ", "腰",
    "上半身", "上半身2", "首", "頭",
    "左肩", "左腕", "左ひじ", "左手首",
    "右肩", "右腕", "右ひじ", "右手首",
    "下半身", "左足", "左ひざ", "左足首",
    "右足", "右ひざ", "右足首",
    "左つま先", "右つま先",
    "左足ＩＫ", "右足ＩＫ", "左つま先ＩＫ", "右つま先ＩＫ",
]


class SetupSkeleton(BaseCommand):
    action = "setup_skeleton"

    def execute(self, params: dict, context: dict) -> dict:
        state: ModelState = context["model_state"]
        state.skeleton.is_configured = True
        state.skeleton.ik_setup = True

        if context.get("bpy_available", False):
            self._create_armature(state, context)

        return {"success": True, "message": f"已配置MMD标准骨骼（{len(MMD_STANDARD_BONES)}根）"}

    def _create_armature(self, state, context):
        pass  # Phase 2b: full Blender armature creation


class AutoWeightPaint(BaseCommand):
    action = "auto_weight_paint"

    def execute(self, params: dict, context: dict) -> dict:
        state: ModelState = context["model_state"]
        if not state.skeleton.is_configured:
            return {"success": False, "error": "请先配置骨骼（setup_skeleton）"}

        if context.get("bpy_available", False):
            self._apply_weights(state, context)

        return {"success": True, "message": "自动权重绘制完成"}

    def _apply_weights(self, state, context):
        pass  # Phase 2b


SKELETON_COMMANDS = [SetupSkeleton, AutoWeightPaint]
```

```python
# commands/physics.py
from commands.base import BaseCommand
from core.model_state import ModelState


class SetupHairPhysics(BaseCommand):
    action = "setup_hair_physics"

    def execute(self, params: dict, context: dict) -> dict:
        state: ModelState = context["model_state"]
        if state.hair is None:
            return {"success": False, "error": "还没有添加头发，请先使用 add_hair"}

        stiffness = params.get("stiffness", 0.5)
        damping = params.get("damping", 0.3)

        state.hair.physics_enabled = True
        state.physics.rigid_body_count += 10  # Placeholder count
        state.physics.joint_count += 9

        if context.get("bpy_available", False):
            self._create_physics(state, stiffness, damping)

        return {"success": True, "message": "头发物理已配置"}

    def _create_physics(self, state, stiffness, damping):
        pass  # Phase 2b


class SetupClothPhysics(BaseCommand):
    action = "setup_cloth_physics"

    def execute(self, params: dict, context: dict) -> dict:
        state: ModelState = context["model_state"]
        index = params.get("index", 0)

        if index < 0 or index >= len(state.clothing):
            return {"success": False, "error": f"服装索引{index}无效"}

        state.clothing[index].physics_enabled = True
        state.physics.rigid_body_count += 8
        state.physics.joint_count += 7

        if context.get("bpy_available", False):
            self._create_cloth_physics(state, index)

        return {"success": True, "message": f"服装物理已配置"}

    def _create_cloth_physics(self, state, index):
        pass  # Phase 2b


PHYSICS_COMMANDS = [SetupHairPhysics, SetupClothPhysics]
```

```python
# commands/morph.py
from commands.base import BaseCommand
from core.model_state import ModelState

STANDARD_EXPRESSIONS = [
    # 眉
    "真面目", "困る", "にこり", "怒り", "上", "下",
    # 目
    "まばたき", "笑い", "ウィンク", "ウィンク右", "ウィンク２",
    # 口
    "あ", "い", "う", "え", "お", "△", "∧", "ω",
    # 其他
    "照れ",
]


class CreateMorph(BaseCommand):
    action = "create_morph"

    def execute(self, params: dict, context: dict) -> dict:
        state: ModelState = context["model_state"]
        name = params.get("name", "")
        if not name:
            return {"success": False, "error": "请指定表情名称(name)"}

        if name not in state.morphs.expressions:
            state.morphs.expressions.append(name)

        return {"success": True, "message": f"已创建表情: {name}"}


class AddExpressionSet(BaseCommand):
    action = "add_expression_set"

    def execute(self, params: dict, context: dict) -> dict:
        state: ModelState = context["model_state"]
        preset = params.get("preset", "standard")

        if preset == "standard":
            expressions = STANDARD_EXPRESSIONS
        else:
            return {"success": False, "error": f"未知表情预设: {preset}，可选: standard"}

        for expr in expressions:
            if expr not in state.morphs.expressions:
                state.morphs.expressions.append(expr)

        return {"success": True, "message": f"已添加{preset}表情集（{len(expressions)}个表情）"}


MORPH_COMMANDS = [CreateMorph, AddExpressionSet]
```

```python
# commands/export.py
from commands.base import BaseCommand
from core.model_state import ModelState


class ValidatePmx(BaseCommand):
    action = "validate_pmx"

    def execute(self, params: dict, context: dict) -> dict:
        state: ModelState = context["model_state"]
        warnings = []

        if not state.skeleton.is_configured:
            warnings.append("骨骼未配置")
        if not state.skeleton.ik_setup:
            warnings.append("IK骨骼未配置")
        if len(state.morphs.expressions) == 0:
            warnings.append("未添加表情")
        if state.hair is None:
            warnings.append("未添加头发")
        if len(state.clothing) == 0:
            warnings.append("未添加服装")

        if warnings:
            return {"success": True, "warnings": warnings,
                    "message": f"验证完成，发现{len(warnings)}个警告: " + ", ".join(warnings)}
        return {"success": True, "warnings": [], "message": "验证通过，模型可以导出"}


class ExportPmx(BaseCommand):
    action = "export_pmx"

    def execute(self, params: dict, context: dict) -> dict:
        if not context.get("bpy_available", False):
            return {"success": False, "error": "导出PMX需要在Blender环境中运行"}

        path = params.get("path", "")
        if not path:
            return {"success": False, "error": "请指定导出路径(path)"}

        # Phase 2b: actual PMX export via mmd_tools
        return {"success": True, "message": f"模型已导出到: {path}"}


EXPORT_COMMANDS = [ValidatePmx, ExportPmx]
```

- [ ] **Step 3: Run all new tests**

Run: `cd E:/Inori_Code/Intrest/AIMoeMaker && python -m pytest tests/test_skeleton_command.py tests/test_physics_command.py tests/test_morph_command.py tests/test_export_command.py -v`
Expected: All 12 PASS

- [ ] **Step 4: Commit**

```bash
git add commands/skeleton.py commands/physics.py commands/morph.py commands/export.py tests/test_skeleton_command.py tests/test_physics_command.py tests/test_morph_command.py tests/test_export_command.py
git commit -m "feat: skeleton, physics, morph, and export commands"
```

---

### Task 6: Register All Commands + Update System Prompt

**Files:**
- Modify: `ui/operators.py` — register all new commands in `get_engine()`
- Modify: `prompts/system_prompt.py` — add all new commands to AI's available command list

- [ ] **Step 1: Update operators.py**

Add imports and registrations for all new command modules. The `get_engine()` function should register:
- `BODY_COMMANDS` (already present)
- `HAIR_COMMANDS` from `commands.hair`
- `FACE_COMMANDS` from `commands.face`
- `CLOTHING_COMMANDS` from `commands.clothing`
- `ACCESSORY_COMMANDS` from `commands.accessory`
- `SKELETON_COMMANDS` from `commands.skeleton`
- `PHYSICS_COMMANDS` from `commands.physics`
- `MORPH_COMMANDS` from `commands.morph`
- `EXPORT_COMMANDS` from `commands.export`

- [ ] **Step 2: Update system_prompt.py**

Add all new commands to the `SYSTEM_PROMPT_ZH` string under their respective categories:
- Hair: add_hair, modify_hair_style, set_hair_color
- Face: set_eye_shape, set_eye_color, adjust_face_shape
- Clothing: add_clothing, modify_clothing, set_fabric_material
- Accessory: add_accessory, remove_accessory
- Skeleton: setup_skeleton, auto_weight_paint
- Physics: setup_hair_physics, setup_cloth_physics
- Morph: create_morph, add_expression_set
- Export: export_pmx, validate_pmx

- [ ] **Step 3: Run full test suite**

Run: `cd E:/Inori_Code/Intrest/AIMoeMaker && python -m pytest tests/ -v`
Expected: All tests PASS (34 old + ~29 new = ~63 total)

- [ ] **Step 4: Commit**

```bash
git add ui/operators.py prompts/system_prompt.py
git commit -m "feat: register all commands and update system prompt"
```
