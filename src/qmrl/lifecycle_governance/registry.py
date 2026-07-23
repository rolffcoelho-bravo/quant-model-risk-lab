"""Unified challenger registry for all validated v1.4 layers."""

from __future__ import annotations

from dataclasses import dataclass

from .domain import ChallengeComponent, evidence_sha256


REQUIRED_COMPONENTS = (
    ChallengeComponent.PORTFOLIO_INGESTION,
    ChallengeComponent.MULTICURRENCY,
    ChallengeComponent.MARGIN_MVA,
    ChallengeComponent.CAPITAL_KVA,
    ChallengeComponent.INCREMENTAL_ALLOCATION,
    ChallengeComponent.OPERATIONS,
)


@dataclass(frozen=True)
class ChallengerSpec:
    component: ChallengeComponent
    challenger_id: str
    primary_method: str
    challenger_method: str
    tolerance: float
    materiality_threshold: float
    required_evidence: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "component", ChallengeComponent(self.component))
        if not self.challenger_id.strip() or not self.primary_method.strip() or not self.challenger_method.strip():
            raise ValueError("Challenger specification identifiers cannot be blank.")
        if self.tolerance < 0.0 or self.materiality_threshold < self.tolerance:
            raise ValueError("Materiality threshold must be at least the reconciliation tolerance.")
        if not self.required_evidence or any(not value.strip() for value in self.required_evidence):
            raise ValueError("Each challenger requires named evidence.")


class ChallengerRegistry:
    def __init__(self, specs: tuple[ChallengerSpec, ...] = ()) -> None:
        self._specs: dict[ChallengeComponent, ChallengerSpec] = {}
        for spec in specs:
            self.register(spec)

    def register(self, spec: ChallengerSpec) -> None:
        if spec.component in self._specs:
            raise ValueError(f"Duplicate challenger component: {spec.component.value}")
        if any(item.challenger_id == spec.challenger_id for item in self._specs.values()):
            raise ValueError(f"Duplicate challenger identifier: {spec.challenger_id}")
        self._specs[spec.component] = spec

    def get(self, component: ChallengeComponent) -> ChallengerSpec:
        try:
            return self._specs[ChallengeComponent(component)]
        except KeyError as exc:
            raise KeyError(f"No challenger registered for {ChallengeComponent(component).value}") from exc

    @property
    def components(self) -> tuple[ChallengeComponent, ...]:
        return tuple(sorted(self._specs, key=lambda item: item.value))

    @property
    def specs(self) -> tuple[ChallengerSpec, ...]:
        return tuple(self._specs[component] for component in self.components)

    def missing(self, required: tuple[ChallengeComponent, ...] = REQUIRED_COMPONENTS) -> tuple[str, ...]:
        return tuple(component.value for component in required if component not in self._specs)

    @property
    def registry_hash(self) -> str:
        return evidence_sha256(self.specs)


def default_registry() -> ChallengerRegistry:
    return ChallengerRegistry(
        tuple(
            ChallengerSpec(
                component=component,
                challenger_id=f"v1_4_{component.value}_independent_challenger",
                primary_method="validated_primary_engine",
                challenger_method="independent_reimplementation_or_reconciliation",
                tolerance=1.0e-9,
                materiality_threshold=1.0e-5,
                required_evidence=("primary_result", "challenger_result", "difference", "status"),
            )
            for component in REQUIRED_COMPONENTS
        )
    )
