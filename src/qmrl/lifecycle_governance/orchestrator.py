"""Unified execution of registered independent challengers."""

from __future__ import annotations

from typing import Mapping, Sequence

from .domain import ChallengeComponent, ChallengeReport
from .reconciliation import component_reconciliation, reconcile_scalar
from .registry import ChallengerRegistry


class ChallengeOrchestrator:
    def __init__(self, registry: ChallengerRegistry) -> None:
        self.registry = registry

    def run_scalar_bundle(
        self,
        run_id: str,
        values: Mapping[ChallengeComponent, tuple[float, float, str]],
    ) -> tuple[ChallengeReport, ...]:
        reports = []
        for component in sorted(values, key=lambda item: ChallengeComponent(item).value):
            primary, challenger, metric = values[component]
            spec = self.registry.get(component)
            reports.append(
                reconcile_scalar(
                    run_id=run_id,
                    metric_name=metric,
                    primary_value=primary,
                    challenger_value=challenger,
                    spec=spec,
                )
            )
        return tuple(reports)

    def run_component_bundle(
        self,
        run_id: str,
        component: ChallengeComponent,
        primary: Mapping[str, float],
        challenger: Mapping[str, float],
    ) -> ChallengeReport:
        return component_reconciliation(
            run_id,
            primary,
            challenger,
            self.registry.get(component),
        )

    def missing_required_components(self) -> tuple[str, ...]:
        return self.registry.missing()
