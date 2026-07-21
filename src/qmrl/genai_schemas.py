"""Structured schemas for governed GenAI model-risk evidence."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


Severity = Literal["low", "medium", "high", "critical"]
Decision = Literal["ALLOW", "CONDITIONAL", "BLOCK"]
FindingCategory = Literal[
    "data",
    "methodology",
    "implementation",
    "validation",
    "monitoring",
    "governance",
    "documentation",
    "model_use",
]


class EvidenceCitation(BaseModel):
    """A reference to evidence supplied to the model."""

    model_config = ConfigDict(extra="forbid")

    source_path: str = Field(min_length=1)
    field_or_excerpt: str = Field(min_length=1)


class GenAIFinding(BaseModel):
    """A structured independent-challenge finding."""

    model_config = ConfigDict(extra="forbid")

    finding_id: str = Field(pattern=r"^GENAI-[0-9]{3}$")
    title: str = Field(min_length=1, max_length=160)
    severity: Severity
    category: FindingCategory
    observed_evidence: str = Field(min_length=1)
    interpretation: str = Field(min_length=1)
    required_action: str = Field(min_length=1)
    citation: EvidenceCitation


class GenAIValidationChallenge(BaseModel):
    """Governed structured output from the GenAI validation challenger."""

    model_config = ConfigDict(extra="forbid")

    evidence_package_id: str = Field(min_length=1)
    decision: Decision
    executive_summary: str = Field(min_length=1)
    supported_use: str = Field(min_length=1)
    prohibited_use: str = Field(min_length=1)
    findings: list[GenAIFinding]
    missing_evidence: list[str]
    human_review_required: bool = True