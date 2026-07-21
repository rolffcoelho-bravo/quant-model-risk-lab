"""OpenAI Responses API adapter for the governed GenAI challenge."""

from __future__ import annotations

from typing import Any

from qmrl.genai_schemas import GenAIValidationChallenge


def run_openai_validation_challenge(
    *,
    model: str,
    prompt: str,
    evidence_package: dict[str, Any],
) -> tuple[GenAIValidationChallenge, dict[str, Any]]:
    """Run the structured validation challenge through the Responses API."""
    from openai import OpenAI

    client = OpenAI()
    response = client.responses.parse(
        model=model,
        input=[
            {
                "role": "system",
                "content": prompt,
            },
            {
                "role": "user",
                "content": (
                    "Review this evidence package:\n\n"
                    + __import__("json").dumps(
                        evidence_package,
                        ensure_ascii=False,
                        sort_keys=True,
                    )
                ),
            },
        ],
        text_format=GenAIValidationChallenge,
    )

    parsed = response.output_parsed
    if parsed is None:
        raise RuntimeError("The provider returned no parsed structured output.")

    usage = getattr(response, "usage", None)
    usage_payload: dict[str, Any] = {}
    if usage is not None:
        if hasattr(usage, "model_dump"):
            usage_payload = usage.model_dump()
        else:
            usage_payload = {
                "input_tokens": getattr(usage, "input_tokens", None),
                "output_tokens": getattr(usage, "output_tokens", None),
                "total_tokens": getattr(usage, "total_tokens", None),
            }

    metadata = {
        "response_id": getattr(response, "id", None),
        "model": model,
        "api": "responses",
        "provider": "openai",
        "usage": usage_payload,
    }
    return parsed, metadata