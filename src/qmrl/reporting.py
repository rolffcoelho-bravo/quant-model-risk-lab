"""Reporting helpers for model-risk validation evidence."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def dataframe_to_markdown(data: pd.DataFrame) -> str:
    """Convert a DataFrame into a simple Markdown table without extra dependencies."""
    if data.empty:
        return "_No records available._"

    columns = [str(column) for column in data.columns]
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"

    rows = []
    for _, row in data.iterrows():
        values = [str(row[column]) for column in data.columns]
        rows.append("| " + " | ".join(values) + " |")

    return "\n".join([header, separator, *rows])


def write_markdown_report(path: str | Path, title: str, sections: dict[str, str]) -> None:
    """Write a Markdown report from named sections."""
    report_path = Path(path)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [f"# {title}", ""]
    for section_title, section_body in sections.items():
        lines.append(f"## {section_title}")
        lines.append("")
        lines.append(section_body.strip())
        lines.append("")

    report_path.write_text("\n".join(lines), encoding="utf-8")


def validation_decision(exception_rate: float, threshold: float) -> str:
    """Return a simple monitoring decision based on exception-rate tolerance."""
    if exception_rate <= threshold:
        return "Pass"
    return "Review required"
