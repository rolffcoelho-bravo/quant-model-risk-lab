"""Build a deterministic GenAI input package from existing FX option evidence."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = REPO_ROOT / "data" / "genai" / "inputs" / "fx_option_validation_evidence.json"

SOURCE_FILES = [
    REPO_ROOT / "reports" / "fx_option_validation_report.md",
    REPO_ROOT / "data" / "official" / "processed" / "fx_option_validation_summary.csv",
    REPO_ROOT / "data" / "official" / "processed" / "fx_option_put_call_parity_table.csv",
    REPO_ROOT / "data" / "official" / "processed" / "fx_option_lifecycle_register.csv",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relative_path(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def csv_records(path: Path) -> list[dict[str, Any]]:
    frame = pd.read_csv(path)
    clean = frame.astype(object).where(pd.notna(frame), None)
    return clean.to_dict(orient="records")


def build_source(path: Path) -> dict[str, Any]:
    source: dict[str, Any] = {
        "path": relative_path(path),
        "sha256": sha256_file(path),
    }

    if path.suffix.lower() == ".csv":
        source["content_type"] = "csv_records"
        source["records"] = csv_records(path)
    else:
        source["content_type"] = "markdown"
        source["content"] = path.read_text(encoding="utf-8-sig")

    return source


def main() -> None:
    missing = [relative_path(path) for path in SOURCE_FILES if not path.exists()]
    if missing:
        raise FileNotFoundError(
            "Required existing repository evidence is missing: "
            + ", ".join(missing)
        )

    evidence_package = {
        "evidence_package_id": "QMRL-GENAI-FXOPTION-001",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "use_case": (
            "Independent GenAI challenge of the existing public FX option "
            "validation evidence."
        ),
        "decision_boundary": {
            "allowed": (
                "GenAI may identify findings, missing evidence and model-use "
                "restrictions."
            ),
            "prohibited": (
                "GenAI may not change pricing results, approve the model, "
                "or create unsupported evidence."
            ),
            "human_review_required": True,
        },
        "sources": [build_source(path) for path in SOURCE_FILES],
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(evidence_package, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    print(f"Wrote {OUTPUT_PATH.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()