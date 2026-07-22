"""Governed proxy hierarchy for counterparty credit calibration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable, Sequence

from .credit_curve import CreditQuote


_ALLOWED_LEVELS = (
    "direct",
    "parent",
    "sovereign",
    "sector",
)


@dataclass(frozen=True)
class CreditProxyCandidate:
    """One candidate spread in the governed proxy hierarchy."""

    candidate_id: str
    obligor_id: str
    proxy_obligor_id: str
    level: str
    tenor_years: float
    spread_bps: float
    basis_adjustment_bps: float
    as_of_date: date
    source_id: str
    probability_measure: str = "risk_neutral"
    currency: str = "USD"
    seniority: str = "senior_unsecured"

    def __post_init__(self) -> None:
        for name in (
            "candidate_id",
            "obligor_id",
            "proxy_obligor_id",
            "source_id",
            "seniority",
        ):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} must not be empty.")
        if self.level not in _ALLOWED_LEVELS:
            raise ValueError("Unsupported proxy level.")
        if self.tenor_years <= 0.0:
            raise ValueError("tenor_years must be positive.")
        if self.spread_bps < 0.0:
            raise ValueError("spread_bps must be non-negative.")
        if len(self.currency.strip()) != 3:
            raise ValueError("currency must be a three-letter code.")

    @property
    def adjusted_spread_bps(self) -> float:
        return float(self.spread_bps + self.basis_adjustment_bps)


@dataclass(frozen=True)
class CreditProxySelection:
    """Auditable result of applying the proxy hierarchy."""

    selected_candidate_id: str
    selected_level: str
    selected_proxy_obligor_id: str
    adjusted_spread_bps: float
    rejected_candidates: tuple[str, ...]
    human_review_required: bool


def select_credit_proxy(
    candidates: Iterable[CreditProxyCandidate],
    *,
    as_of_date: date,
    max_age_days: int,
    required_tenor: float,
    expected_measure: str,
    expected_currency: str,
    expected_seniority: str,
    allowed_levels: Sequence[str] = _ALLOWED_LEVELS,
) -> CreditProxySelection:
    """Select the highest-priority eligible proxy and preserve rejections."""

    if max_age_days < 0:
        raise ValueError("max_age_days must be non-negative.")
    if required_tenor <= 0.0:
        raise ValueError("required_tenor must be positive.")

    allowed = tuple(allowed_levels)
    if not allowed or any(level not in _ALLOWED_LEVELS for level in allowed):
        raise ValueError("allowed_levels contains an unsupported level.")

    priority = {level: index for index, level in enumerate(allowed)}
    eligible: list[CreditProxyCandidate] = []
    rejected: list[str] = []

    for candidate in candidates:
        reason: str | None = None
        age = (as_of_date - candidate.as_of_date).days

        if candidate.level not in priority:
            reason = "level_not_allowed"
        elif age < 0:
            reason = "future_dated"
        elif age > max_age_days:
            reason = "stale"
        elif abs(candidate.tenor_years - required_tenor) > 1e-12:
            reason = "tenor_mismatch"
        elif candidate.probability_measure != expected_measure:
            reason = "measure_mismatch"
        elif candidate.currency.upper() != expected_currency.upper():
            reason = "currency_mismatch"
        elif candidate.seniority != expected_seniority:
            reason = "seniority_mismatch"
        elif candidate.adjusted_spread_bps < 0.0:
            reason = "negative_adjusted_spread"

        if reason is None:
            eligible.append(candidate)
        else:
            rejected.append(f"{candidate.candidate_id}:{reason}")

    if not eligible:
        raise ValueError("No eligible credit proxy candidate is available.")

    eligible.sort(
        key=lambda candidate: (
            priority[candidate.level],
            -candidate.as_of_date.toordinal(),
            candidate.candidate_id,
        )
    )
    selected = eligible[0]

    return CreditProxySelection(
        selected_candidate_id=selected.candidate_id,
        selected_level=selected.level,
        selected_proxy_obligor_id=selected.proxy_obligor_id,
        adjusted_spread_bps=selected.adjusted_spread_bps,
        rejected_candidates=tuple(sorted(rejected)),
        human_review_required=(selected.level != "direct"),
    )


def proxy_selection_to_quote(
    selection: CreditProxySelection,
    *,
    quote_id: str,
    obligor_id: str,
    tenor_years: float,
    as_of_date: date,
    source_id: str,
    probability_measure: str,
    currency: str,
    seniority: str,
) -> CreditQuote:
    """Convert an approved proxy selection into a governed proxy quote."""

    return CreditQuote(
        quote_id=quote_id,
        obligor_id=obligor_id,
        tenor_years=tenor_years,
        spread_bps=selection.adjusted_spread_bps,
        as_of_date=as_of_date,
        source_id=source_id,
        quote_type="proxy",
        probability_measure=probability_measure,
        currency=currency,
        seniority=seniority,
    )
