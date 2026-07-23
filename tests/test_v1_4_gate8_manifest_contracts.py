from __future__ import annotations
import json
from pathlib import Path
import yaml
from qmrl.release_consolidation import normalized_sha256

ROOT = Path(".")

def manifest():
    return json.loads((ROOT / "configs/release_manifest_v1_4_gate8.json").read_text(encoding="utf-8"))

def test_gate8_manifest_test_surface():
    value = manifest()
    assert value["validation"]["prior_collected_test_count"] == 666
    assert value["validation"]["new_test_count"] == 42
    assert value["validation"]["collected_test_count"] == 708

def test_gate8_manifest_base_commit_and_target():
    value = manifest()
    assert value["base_main_commit"] == "f433475"
    assert value["target_status"] == "RELEASED_WITH_MONITORING"

def test_gate8_manifest_hashes_reconcile():
    assert all(normalized_sha256(ROOT / item["path"]) == item["sha256"] for item in manifest()["artifacts"])

def test_release_contract_requires_two_human_tokens():
    contract = yaml.safe_load((ROOT / "configs/v1_4_release_contract.yml").read_text(encoding="utf-8"))
    assert contract["required_human_tokens"] == {"pull_request_merge": "SQUASH", "publication": "RELEASE"}

def test_publication_contract_blocks_autonomous_genai():
    contract = yaml.safe_load((ROOT / "configs/v1_4_publication_contract.yml").read_text(encoding="utf-8"))
    assert contract["autonomous_genai_publication"] is False
    assert contract["human_release_approval_required"] is True

def test_v1_4_readme_and_release_notes_are_consolidated():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    notes = (ROOT / "docs/releases/v1.4.0.md").read_text(encoding="utf-8")
    assert "Latest governed release: v1.4.0" in readme
    assert "708 collected tests" in readme
    assert "Validated collected tests:** `708`" in notes
