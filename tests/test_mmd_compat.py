from pipeline.mmd_tools_compat import get_install_guidance, check_mmd_tools_or_report


def test_install_guidance_is_chinese():
    guidance = get_install_guidance()
    assert "mmd_tools" in guidance
    assert "安装" in guidance
    assert "github" in guidance.lower()


def test_check_reports_unavailable():
    # In test environment, mmd_tools won't be installed
    result = check_mmd_tools_or_report()
    assert result["available"] is False
    assert "guidance" in result
