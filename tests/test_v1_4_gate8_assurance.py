from __future__ import annotations
from qmrl.release_consolidation import AssuranceCheck, CheckStatus, assess_release, post_release_checks, standard_pre_release_checks

def test_release_requires_human_approval():
    result = assess_release(standard_pre_release_checks(), human_release_approval=False)
    assert result.status == "RELEASE_APPROVAL_REQUIRED"

def test_monitoring_check_produces_release_with_monitoring():
    result = assess_release(standard_pre_release_checks(), human_release_approval=True)
    assert result.status == "RELEASED_WITH_MONITORING"

def test_material_block_prevents_release():
    check = AssuranceCheck("b", CheckStatus.BLOCK, "material", True)
    assert assess_release((check,), human_release_approval=True).status == "BLOCK"

def test_remediation_prevents_release():
    check = AssuranceCheck("r", CheckStatus.REMEDIATE, "open")
    assert assess_release((check,), human_release_approval=True).status == "REMEDIATE"

def test_post_release_checks_pass_complete_state():
    checks = post_release_checks(tag_matches=True, release_published=True, assurance_tests_pass=True, v13_preserved=True, clean_tree=True)
    assert all(item.status == CheckStatus.PASS for item in checks)

def test_post_release_check_blocks_failed_tag_target():
    checks = post_release_checks(tag_matches=False, release_published=True, assurance_tests_pass=True, v13_preserved=True, clean_tree=True)
    assert checks[0].status == CheckStatus.BLOCK and checks[0].material
