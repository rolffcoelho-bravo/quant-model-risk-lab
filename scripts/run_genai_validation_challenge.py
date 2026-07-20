"""Run and govern the GenAI independent validation challenge."""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = REPO_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from qmrl.genai_client import run_openai_validation_challenge
from qmrl.genai_grounding import validate_grounding


CONFIG_PATH = REPO_ROOT / "configs" / "genai_validation_contract.json"
PROMPT_PATH = (
    REPO_ROOT / "prompts" / "genai" / "independent_validation_challenge_v1.md"
)
INPUT_PATH = (
    REPO_ROOT / "data" / "genai" / "inputs" / "fx_option_validation_evidence.json"
)
OUTPUT_PATH = (
    REPO_ROOT / "data" / "genai" / "outputs" / "fx_option_validation_challenge.json"
)
MANIFEST_PATH = (
    REPO_ROOT / "data" / "genai" / "outputs" / "fx_option_validation_run_manifest.json"
)
REPORT_PATH = (
    REPO_ROOT / "reports" / "genai" / "fx_option_genai_validation_challenge.md"
)


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def build_report(
    response: dict[str, Any],
    grounding_issues: list[str],
    metadata: dict[str, Any],
) -> str:
    findings = response.get("findings", [])
    lines = [
        "# GenAI Independent Validation Challenge",
        "",
        f"Evidence package: `{response['evidence_package_id']}`",
        f"Provider: `{metadata['provider']}`",
        f"API: `{metadata['api']}`",
        f"Model: `{metadata['model']}`",
        f"Decision: **{response['decision']}**",
        f"Grounding gate: **{'PASS' if not grounding_issues else 'FAIL'}**",
        "",
        "## Executive summary",
        "",
        response["executive_summary"],
        "",
        "## Supported use",
        "",
        response["supported_use"],
        "",
        "## Prohibited use",
        "",
        response["prohibited_use"],
        "",
        "## Findings",
        "",
    ]

    if not findings:
        lines.append("No findings were returned.")
    else:
        for finding in findings:
            lines.extend(
                [
                    f"### {finding['finding_id']} | {finding['title']}",
                    "",
                    f"- Severity: `{finding['severity']}`",
                    f"- Category: `{finding['category']}`",
                    f"- Source: `{finding['citation']['source_path']}`",
                    f"- Evidence: {finding['observed_evidence']}",
                    f"- Interpretation: {finding['interpretation']}",
                    f"- Required action: {finding['required_action']}",
                    "",
                ]
            )

    lines.extend(["## Missing evidence", ""])
    missing = response.get("missing_evidence", [])
    if missing:
        lines.extend([f"- {item}" for item in missing])
    else:
        lines.append("- None identified.")

    lines.extend(["", "## Deterministic grounding controls", ""])
    if grounding_issues:
        lines.extend([f"- FAIL: {issue}" for issue in grounding_issues])
    else:
        lines.append("- PASS: all citations resolve to supplied sources.")
        lines.append("- PASS: no unsupported numeric claim was detected.")
        lines.append("- PASS: the mandatory human-review gate is preserved.")

    lines.extend(
        [
            "",
            "## Governance statement",
            "",
            (
                "This GenAI output is challenger evidence only. It does not alter "
                "the deterministic pricing model, replace independent validation, "
                "or constitute formal model approval."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    for path in [CONFIG_PATH, PROMPT_PATH, INPUT_PATH]:
        if not path.exists():
            raise FileNotFoundError(f"Required file not found: {path}")

    config = read_json(CONFIG_PATH)
    prompt_bytes = PROMPT_PATH.read_bytes()
    input_bytes = INPUT_PATH.read_bytes()
    prompt = prompt_bytes.decode("utf-8-sig")
    evidence_package = json.loads(input_bytes.decode("utf-8-sig"))

    model_var = config["model_environment_variable"]
    model = os.getenv(model_var, config["default_model"])

    challenge, metadata = run_openai_validation_challenge(
        model=model,
        prompt=prompt,
        evidence_package=evidence_package,
    )

    grounding_issues = validate_grounding(challenge, evidence_package)
    response_payload = challenge.model_dump(mode="json")
    response_bytes = json.dumps(
        response_payload,
        indent=2,
        ensure_ascii=False,
        sort_keys=True,
    ).encode("utf-8")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_bytes(response_bytes)

    manifest = {
        "run_id": "QMRL-GENAI-RUN-001",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_package_id": evidence_package["evidence_package_id"],
        "provider": metadata["provider"],
        "api": metadata["api"],
        "model": metadata["model"],
        "provider_response_id": metadata["response_id"],
        "usage": metadata["usage"],
        "input_path": INPUT_PATH.relative_to(REPO_ROOT).as_posix(),
        "input_sha256": sha256_bytes(input_bytes),
        "prompt_path": PROMPT_PATH.relative_to(REPO_ROOT).as_posix(),
        "prompt_sha256": sha256_bytes(prompt_bytes),
        "output_path": OUTPUT_PATH.relative_to(REPO_ROOT).as_posix(),
        "output_sha256": sha256_bytes(response_bytes),
        "grounding_gate": "PASS" if not grounding_issues else "FAIL",
        "grounding_issues": grounding_issues,
        "human_review_required": True,
    }
    MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )

    report = build_report(response_payload, grounding_issues, metadata)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")

    print(f"Wrote {OUTPUT_PATH.relative_to(REPO_ROOT)}")
    print(f"Wrote {MANIFEST_PATH.relative_to(REPO_ROOT)}")
    print(f"Wrote {REPORT_PATH.relative_to(REPO_ROOT)}")
    print(f"Grounding gate: {manifest['grounding_gate']}")

    if grounding_issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()