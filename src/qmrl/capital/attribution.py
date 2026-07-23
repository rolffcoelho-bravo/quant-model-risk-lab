from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

import numpy as np

from .capital_profile import CapitalProfileResult
from .kva import KVAResult


@dataclass(frozen=True)
class CapitalAttribution:
    netting_set: tuple[dict[str, object], ...]
    counterparty: tuple[dict[str, object], ...]
    currency: tuple[dict[str, object], ...]
    trade: tuple[dict[str, object], ...]
    time_bucket: tuple[dict[str, object], ...]
    reconciliation_residual: float


def build_capital_attribution(
    profile: CapitalProfileResult,
    kva: KVAResult,
) -> CapitalAttribution:
    source = profile.exposure_input
    netting_rows = tuple(
        {
            "netting_set_id": source.netting_set_ids[index],
            "counterparty_id": source.counterparty_ids[index],
            "currency": source.currencies[index],
            "kva": float(kva.netting_set_kva[index]),
            "peak_capital": float(np.max(profile.capital_profiles[index])),
        }
        for index in range(source.netting_set_count)
    )

    counterparty_totals: defaultdict[str, float] = defaultdict(float)
    currency_totals: defaultdict[str, float] = defaultdict(float)
    for index, value in enumerate(kva.netting_set_kva):
        counterparty_totals[source.counterparty_ids[index]] += float(value)
        currency_totals[source.currencies[index]] += float(value)

    counterparty_rows = tuple(
        {"counterparty_id": key, "kva": value}
        for key, value in sorted(counterparty_totals.items())
    )
    currency_rows = tuple(
        {"currency": key, "kva": value}
        for key, value in sorted(currency_totals.items())
    )

    trade_rows: list[dict[str, object]] = []
    for trade_id, set_index, weight in zip(
        source.trade_ids,
        source.trade_netting_set_indices,
        source.trade_weights,
        strict=True,
    ):
        trade_rows.append(
            {
                "trade_id": trade_id,
                "netting_set_id": source.netting_set_ids[set_index],
                "weight": float(weight),
                "kva": float(kva.netting_set_kva[set_index] * weight),
            }
        )

    time_rows = tuple(
        {
            "start": float(source.times[index]),
            "end": float(source.times[index + 1]),
            "kva": float(kva.interval_contributions[:, index].sum()),
        }
        for index in range(len(source.times) - 1)
    )

    residual = float(kva.total_kva - sum(float(row["kva"]) for row in netting_rows))
    return CapitalAttribution(
        netting_set=netting_rows,
        counterparty=counterparty_rows,
        currency=currency_rows,
        trade=tuple(trade_rows),
        time_bucket=time_rows,
        reconciliation_residual=residual,
    )


def capital_concentration(profile: CapitalProfileResult, kva: KVAResult) -> dict[str, float]:
    values = np.maximum(kva.netting_set_kva, 0.0)
    total = float(values.sum())
    if total == 0.0:
        return {"hhi": 0.0, "maximum_share": 0.0, "peak_capital": profile.peak_capital}
    shares = values / total
    return {
        "hhi": float(np.sum(shares**2)),
        "maximum_share": float(np.max(shares)),
        "peak_capital": profile.peak_capital,
    }
