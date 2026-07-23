from __future__ import annotations

from qmrl.portfolio import (
    AgreementTerms,
    CollateralSet,
    Counterparty,
    CurrencyDefinition,
    LegalEntity,
    NettingSet,
    PortfolioSnapshot,
    TradeRecord,
)
from qmrl.multicurrency import (
    CollateralProfile,
    CurrencyCurveSet,
    FXQuote,
    FXScenarioMarket,
    MultiCurrencyPolicy,
    PathwiseSeries,
    TermCurve,
)


TIMES = (0.0, 1.0)


def reference_snapshot() -> PortfolioSnapshot:
    return PortfolioSnapshot(
        snapshot_id="SNAP-G2",
        valuation_date="2026-07-23",
        reporting_currency="USD",
        currencies=(
            CurrencyDefinition("USD"),
            CurrencyDefinition("EUR"),
            CurrencyDefinition("GBP"),
        ),
        legal_entities=(
            LegalEntity("LE-1", "Reference Bank", "USD"),
        ),
        counterparties=(
            Counterparty("CP-1", "Reference Counterparty"),
        ),
        agreements=(
            AgreementTerms(
                agreement_id="AGR-1",
                threshold=0.0,
                minimum_transfer_amount=0.0,
                eligible_collateral_currencies=("USD", "EUR", "GBP"),
            ),
        ),
        netting_sets=(
            NettingSet("NS-1", "CP-1", "LE-1", "AGR-1"),
        ),
        collateral_sets=(
            CollateralSet(
                "CS-1",
                "NS-1",
                "AGR-1",
                ("USD", "EUR", "GBP"),
            ),
        ),
        trades=(
            TradeRecord(
                trade_id="T-USD",
                product_type="swap",
                legal_entity_id="LE-1",
                counterparty_id="CP-1",
                netting_set_id="NS-1",
                collateral_set_id="CS-1",
                trade_currency="USD",
                settlement_currency="USD",
                notional=100.0,
                effective_date="2026-07-23",
                maturity_date="2028-07-23",
            ),
            TradeRecord(
                trade_id="T-EUR",
                product_type="forward",
                legal_entity_id="LE-1",
                counterparty_id="CP-1",
                netting_set_id="NS-1",
                collateral_set_id="CS-1",
                trade_currency="EUR",
                settlement_currency="EUR",
                notional=100.0,
                effective_date="2026-07-23",
                maturity_date="2028-07-23",
            ),
        ),
    )


def trade_values(
    *,
    usd=((100.0, 80.0), (-20.0, 10.0)),
    eur=((10.0, 20.0), (10.0, -20.0)),
):
    return {
        "T-USD": PathwiseSeries("USD", TIMES, usd),
        "T-EUR": PathwiseSeries("EUR", TIMES, eur),
    }


def fx_market() -> FXScenarioMarket:
    return FXScenarioMarket(
        (
            FXQuote(
                "EUR",
                "USD",
                TIMES,
                ((1.10, 1.20), (1.10, 1.20)),
            ),
            FXQuote(
                "GBP",
                "EUR",
                TIMES,
                ((1.20, 1.25), (1.20, 1.25)),
            ),
            FXQuote(
                "GBP",
                "USD",
                TIMES,
                ((1.32, 1.50), (1.32, 1.50)),
            ),
        ),
        triangulation_currency="EUR",
    )


def curves() -> CurrencyCurveSet:
    result = []
    for currency in ("USD", "EUR", "GBP"):
        result.extend(
            (
                TermCurve(
                    f"{currency}-DISC",
                    currency,
                    "discount",
                    TIMES,
                    (1.0, 0.95),
                ),
                TermCurve(
                    f"{currency}-FUND",
                    currency,
                    "funding",
                    TIMES,
                    (0.01, 0.012),
                ),
                TermCurve(
                    f"{currency}-COLL",
                    currency,
                    "collateral_remuneration",
                    TIMES,
                    (0.0, 0.0),
                ),
            )
        )
    return CurrencyCurveSet(result)


def collateral(
    currency="USD",
    balances=((20.0, 20.0), (20.0, 20.0)),
    rates=None,
) -> dict[str, CollateralProfile]:
    return {
        "CS-1": CollateralProfile(
            "CS-1",
            currency,
            TIMES,
            balances,
            rates,
        )
    }


def policy() -> MultiCurrencyPolicy:
    return MultiCurrencyPolicy(
        reporting_currency="USD",
        triangulation_currency="EUR",
    )
