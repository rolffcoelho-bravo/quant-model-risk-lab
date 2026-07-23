from __future__ import annotations
import pytest
from qmrl.release_consolidation import previous_release_preserved, publication_payload, release_title, required_disclosures, validate_tag_name

def test_release_tag_is_v1_4_0():
    assert validate_tag_name("v1.4.0") == "v1.4.0"

def test_other_release_tag_is_rejected():
    with pytest.raises(ValueError, match="v1.4.0"):
        validate_tag_name("v1.4.1")

def test_release_title_is_stable():
    assert release_title() == "Quant Model Risk Lab v1.4.0"

def test_publication_payload_discloses_boundaries():
    payload = publication_payload(commit_sha="abcdef123", test_count=708)
    assert required_disclosures(payload) == ()

def test_publication_payload_rejects_nonpositive_test_count():
    with pytest.raises(ValueError, match="positive"):
        publication_payload(commit_sha="abcdef123", test_count=0)

def test_previous_release_tag_is_preserved():
    assert previous_release_preserved(("v1.3.0", "v1.4.0"))
