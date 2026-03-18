from pipeline.mmd_tools_compat import get_install_guidance, check_mmd_tools_or_report
from pipeline.skeleton_setup import REQUIRED_BONES
from pipeline.morph_setup import REQUIRED_MORPHS


def test_install_guidance_is_chinese():
    guidance = get_install_guidance()
    assert "mmd_tools" in guidance
    assert "安装" in guidance


def test_check_reports_unavailable():
    result = check_mmd_tools_or_report()
    assert result["available"] is False
    assert "guidance" in result


def test_required_bones_complete():
    assert "全ての親" in REQUIRED_BONES
    assert "センター" in REQUIRED_BONES
    assert "左足ＩＫ" in REQUIRED_BONES
    assert "右足ＩＫ" in REQUIRED_BONES
    assert len(REQUIRED_BONES) >= 20


def test_required_morphs_defined():
    assert "eye" in REQUIRED_MORPHS
    assert "mouth" in REQUIRED_MORPHS
    assert "まばたき" in REQUIRED_MORPHS["eye"]
    assert "あ" in REQUIRED_MORPHS["mouth"]
