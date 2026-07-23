"""MVA aggregation, attribution, and concentration diagnostics."""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from .domain import MVAAggregation, MVAResult


def aggregate_mva(results: Iterable[MVAResult]) -> MVAAggregation:
    items = tuple(results)
    posted = sum(item.posted_mva for item in items)
    benefit = sum(item.received_margin_benefit for item in items)
    by_netting: dict[str, float] = defaultdict(float)
    by_currency: dict[str, float] = defaultdict(float)
    bucket_count = max((len(item.buckets) for item in items), default=0)
    buckets = [0.0] * bucket_count
    weights: list[float] = []
    for item in items:
        by_netting[item.netting_set_id] += item.net_mva
        by_currency[item.currency] += item.net_mva
        weights.append(abs(item.posted_mva))
        for index, bucket in enumerate(item.buckets):
            buckets[index] += bucket.net_mva
    total_weight = sum(weights)
    if total_weight > 0.0:
        shares = [value / total_weight for value in weights]
        hhi = sum(share * share for share in shares)
        maximum = max(shares)
    else:
        hhi = 0.0
        maximum = 0.0
    return MVAAggregation(
        posted_mva=posted,
        received_margin_benefit=benefit,
        net_mva=posted - benefit,
        by_netting_set=dict(sorted(by_netting.items())),
        by_currency=dict(sorted(by_currency.items())),
        bucket_net_mva=tuple(buckets),
        concentration_hhi=hhi,
        maximum_share=maximum,
    )
