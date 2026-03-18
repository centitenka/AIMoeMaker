# pipeline/morph_setup.py
"""
Stage 5: Verify morph (shape key) setup for PMX export.
"""

REQUIRED_MORPHS = {
    "eye": ["まばたき"],
    "mouth": ["あ"],
}


def verify_morphs(body_obj) -> dict:
    """
    Verify shape keys exist and are properly configured.
    """
    if body_obj is None or body_obj.type != 'MESH':
        return {"success": False, "warnings": ["未找到网格对象"]}

    warnings = []
    morph_count = 0

    if body_obj.data.shape_keys is None:
        warnings.append("未创建任何表情（Shape Key）")
        return {"success": False, "warnings": warnings, "morph_count": 0}

    existing = set(sk.name for sk in body_obj.data.shape_keys.key_blocks)
    morph_count = len(existing) - 1  # Exclude "Basis"

    for category, required in REQUIRED_MORPHS.items():
        for name in required:
            if name not in existing:
                warnings.append(f"缺少必要表情: {name} ({category})")

    return {
        "success": len(warnings) == 0,
        "warnings": warnings,
        "morph_count": morph_count,
    }
