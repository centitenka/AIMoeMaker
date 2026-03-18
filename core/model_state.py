"""
ModelState dataclass – tracks the current state of the 3D model being built.
Pure Python, no bpy dependency.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional


# ---------------------------------------------------------------------------
# Sub-state dataclasses
# ---------------------------------------------------------------------------

@dataclass
class BodyState:
    height: float = 158.0
    body_type: str = "default"
    chest_size: str = "medium"
    waist_ratio: float = 0.65
    hip_ratio: float = 1.0
    leg_length_ratio: float = 0.5
    # Proportion sliders (0.0–1.0 normalized values)
    bust: float = 0.5
    waist: float = 0.5
    hip: float = 0.5
    head_ratio: float = 0.5

    def to_dict(self) -> dict:
        return {
            "height": self.height,
            "body_type": self.body_type,
            "chest_size": self.chest_size,
            "waist_ratio": self.waist_ratio,
            "hip_ratio": self.hip_ratio,
            "leg_length_ratio": self.leg_length_ratio,
            "bust": self.bust,
            "waist": self.waist,
            "hip": self.hip,
            "head_ratio": self.head_ratio,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "BodyState":
        known = {
            "height", "body_type", "chest_size",
            "waist_ratio", "hip_ratio", "leg_length_ratio",
            "bust", "waist", "hip", "head_ratio",
        }
        kwargs = {k: v for k, v in d.items() if k in known}
        return cls(**kwargs)


@dataclass
class HairState:
    style: str = "none"
    length: str = "medium"
    color: str = "black"
    has_ahoge: bool = False
    has_twintails: bool = False
    accessory: str = "none"

    def to_dict(self) -> dict:
        return {
            "style": self.style,
            "length": self.length,
            "color": self.color,
            "has_ahoge": self.has_ahoge,
            "has_twintails": self.has_twintails,
            "accessory": self.accessory,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "HairState":
        known = {
            "style", "length", "color",
            "has_ahoge", "has_twintails", "accessory",
        }
        kwargs = {k: v for k, v in d.items() if k in known}
        return cls(**kwargs)


@dataclass
class FaceState:
    face_shape: str = "oval"
    eye_style: str = "normal"
    eye_color: str = "brown"
    nose_style: str = "normal"
    mouth_style: str = "normal"
    skin_tone: str = "fair"

    def to_dict(self) -> dict:
        return {
            "face_shape": self.face_shape,
            "eye_style": self.eye_style,
            "eye_color": self.eye_color,
            "nose_style": self.nose_style,
            "mouth_style": self.mouth_style,
            "skin_tone": self.skin_tone,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "FaceState":
        known = {
            "face_shape", "eye_style", "eye_color",
            "nose_style", "mouth_style", "skin_tone",
        }
        kwargs = {k: v for k, v in d.items() if k in known}
        return cls(**kwargs)


@dataclass
class ClothingItem:
    slot: str = "top"
    style: str = "none"
    color: str = "white"
    material: str = "cotton"

    def to_dict(self) -> dict:
        return {
            "slot": self.slot,
            "style": self.style,
            "color": self.color,
            "material": self.material,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ClothingItem":
        known = {"slot", "style", "color", "material"}
        kwargs = {k: v for k, v in d.items() if k in known}
        return cls(**kwargs)


@dataclass
class AccessoryItem:
    name: str = "none"
    slot: str = "head"
    position: list = field(default_factory=lambda: [0.0, 0.0, 0.0])
    scale: float = 1.0

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "slot": self.slot,
            "position": list(self.position),
            "scale": self.scale,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "AccessoryItem":
        known = {"name", "slot", "position", "scale"}
        kwargs = {k: v for k, v in d.items() if k in known}
        if "position" in kwargs:
            kwargs["position"] = list(kwargs["position"])
        return cls(**kwargs)


@dataclass
class SkeletonState:
    rig_type: str = "standard"
    has_ik: bool = True
    has_finger_bones: bool = True
    has_facial_bones: bool = True
    spine_count: int = 3

    def to_dict(self) -> dict:
        return {
            "rig_type": self.rig_type,
            "has_ik": self.has_ik,
            "has_finger_bones": self.has_finger_bones,
            "has_facial_bones": self.has_facial_bones,
            "spine_count": self.spine_count,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "SkeletonState":
        known = {
            "rig_type", "has_ik", "has_finger_bones",
            "has_facial_bones", "spine_count",
        }
        kwargs = {k: v for k, v in d.items() if k in known}
        return cls(**kwargs)


@dataclass
class PhysicsState:
    has_cloth_sim: bool = False
    has_hair_physics: bool = False
    has_breast_physics: bool = False
    cloth_quality: str = "medium"

    def to_dict(self) -> dict:
        return {
            "has_cloth_sim": self.has_cloth_sim,
            "has_hair_physics": self.has_hair_physics,
            "has_breast_physics": self.has_breast_physics,
            "cloth_quality": self.cloth_quality,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "PhysicsState":
        known = {
            "has_cloth_sim", "has_hair_physics",
            "has_breast_physics", "cloth_quality",
        }
        kwargs = {k: v for k, v in d.items() if k in known}
        return cls(**kwargs)


@dataclass
class MorphState:
    has_lip_sync: bool = False
    has_eye_blink: bool = False
    has_emotion_morphs: bool = False
    custom_morphs: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "has_lip_sync": self.has_lip_sync,
            "has_eye_blink": self.has_eye_blink,
            "has_emotion_morphs": self.has_emotion_morphs,
            "custom_morphs": list(self.custom_morphs),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "MorphState":
        known = {
            "has_lip_sync", "has_eye_blink",
            "has_emotion_morphs", "custom_morphs",
        }
        kwargs = {k: v for k, v in d.items() if k in known}
        if "custom_morphs" in kwargs:
            kwargs["custom_morphs"] = list(kwargs["custom_morphs"])
        return cls(**kwargs)


# ---------------------------------------------------------------------------
# Top-level ModelState
# ---------------------------------------------------------------------------

@dataclass
class ModelState:
    SCHEMA_VERSION: int = field(default=1, init=False, repr=False, compare=False)

    body: BodyState = field(default_factory=BodyState)
    face: FaceState = field(default_factory=FaceState)
    hair: Optional[HairState] = None
    clothing: list = field(default_factory=list)
    accessories: list = field(default_factory=list)
    skeleton: SkeletonState = field(default_factory=SkeletonState)
    physics: PhysicsState = field(default_factory=PhysicsState)
    morphs: MorphState = field(default_factory=MorphState)
    model_name: str = "新角色"
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "schema_version": 1,
            "model_name": self.model_name,
            "notes": self.notes,
            "body": self.body.to_dict(),
            "face": self.face.to_dict(),
            "hair": self.hair.to_dict() if self.hair is not None else None,
            "clothing": [c.to_dict() for c in self.clothing],
            "accessories": [a.to_dict() for a in self.accessories],
            "skeleton": self.skeleton.to_dict(),
            "physics": self.physics.to_dict(),
            "morphs": self.morphs.to_dict(),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ModelState":
        state = cls()

        if "model_name" in d:
            state.model_name = d["model_name"]
        if "notes" in d:
            state.notes = d["notes"]

        if "body" in d and d["body"] is not None:
            state.body = BodyState.from_dict(d["body"])
        if "face" in d and d["face"] is not None:
            state.face = FaceState.from_dict(d["face"])
        if "hair" in d and d["hair"] is not None:
            state.hair = HairState.from_dict(d["hair"])
        else:
            state.hair = None

        if "clothing" in d and d["clothing"] is not None:
            state.clothing = [ClothingItem.from_dict(c) for c in d["clothing"]]
        if "accessories" in d and d["accessories"] is not None:
            state.accessories = [AccessoryItem.from_dict(a) for a in d["accessories"]]

        if "skeleton" in d and d["skeleton"] is not None:
            state.skeleton = SkeletonState.from_dict(d["skeleton"])
        if "physics" in d and d["physics"] is not None:
            state.physics = PhysicsState.from_dict(d["physics"])
        if "morphs" in d and d["morphs"] is not None:
            state.morphs = MorphState.from_dict(d["morphs"])

        return state

    def to_summary(self) -> str:
        """Return a Chinese-language text summary suitable for AI prompt context."""
        lines = [f"模型名称: {self.model_name}"]

        # 身体
        b = self.body
        lines.append(
            f"身体: 身高 {b.height}cm, 体型 {b.body_type}, "
            f"胸部 {b.chest_size}, 腰比 {b.waist_ratio}, 腿比 {b.leg_length_ratio}"
        )

        # 脸
        f = self.face
        lines.append(
            f"脸型: {f.face_shape}, 眼睛 {f.eye_style}({f.eye_color}), 肤色 {f.skin_tone}"
        )

        # 头发
        if self.hair is not None:
            h = self.hair
            extra = []
            if h.has_ahoge:
                extra.append("呆毛")
            if h.has_twintails:
                extra.append("双马尾")
            extra_str = "、".join(extra) if extra else "无特殊"
            lines.append(
                f"头发: {h.style}, 长度 {h.length}, 颜色 {h.color}, 特征 {extra_str}"
            )
        else:
            lines.append("头发: 未设置")

        # 服装
        if self.clothing:
            clothing_strs = [f"{c.slot}({c.style}/{c.color})" for c in self.clothing]
            lines.append("服装: " + ", ".join(clothing_strs))
        else:
            lines.append("服装: 未设置")

        # 配件
        if self.accessories:
            acc_strs = [f"{a.name}@{a.slot}" for a in self.accessories]
            lines.append("配件: " + ", ".join(acc_strs))

        # 骨骼
        sk = self.skeleton
        lines.append(
            f"骨骼: {sk.rig_type}, IK={'是' if sk.has_ik else '否'}, "
            f"手指骨={'是' if sk.has_finger_bones else '否'}"
        )

        # 物理
        ph = self.physics
        phys_parts = []
        if ph.has_cloth_sim:
            phys_parts.append("布料")
        if ph.has_hair_physics:
            phys_parts.append("头发物理")
        if ph.has_breast_physics:
            phys_parts.append("胸部物理")
        lines.append("物理: " + (", ".join(phys_parts) if phys_parts else "未启用"))

        # 变形
        mo = self.morphs
        morph_parts = []
        if mo.has_lip_sync:
            morph_parts.append("口型同步")
        if mo.has_eye_blink:
            morph_parts.append("眨眼")
        if mo.has_emotion_morphs:
            morph_parts.append("表情变形")
        lines.append("变形: " + (", ".join(morph_parts) if morph_parts else "未启用"))

        if self.notes:
            lines.append(f"备注: {self.notes}")

        return "\n".join(lines)
