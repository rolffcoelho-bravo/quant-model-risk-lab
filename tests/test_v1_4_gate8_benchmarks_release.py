from __future__ import annotations
from pathlib import Path
import json
from qmrl.release_consolidation import benchmark_evidence, run_gate8_benchmarks

def test_gate8_has_ten_locked_benchmarks():
    assert len(run_gate8_benchmarks()) == 10

def test_all_gate8_benchmarks_pass():
    assert all(item.status == "PASS" for item in run_gate8_benchmarks())

def test_benchmark_evidence_is_complete():
    evidence = benchmark_evidence()
    assert evidence["gate"] == 8 and evidence["benchmark_count"] == 10

def test_benchmark_evidence_confirms_expected_behaviour():
    assert benchmark_evidence()["all_expected_behaviour_confirmed"] is True

def test_human_review_blocks_genai_release_approval():
    review = json.loads(Path("data/release/v1_4_human_review.json").read_text(encoding="utf-8"))
    assert review["genai_may_approve_release"] is False
    assert review["required_release_token"] == "RELEASE"

def test_genai_disposition_remains_advisory_only():
    record = json.loads(Path("data/genai/outputs/v1_4_genai_challenge_disposition.json").read_text(encoding="utf-8"))
    assert record["role"] == "advisory_evidence_challenge"
    assert record["promoted_release"] is False
