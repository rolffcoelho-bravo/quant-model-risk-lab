from qmrl.allocation import (
    AdjustmentVector,
    PortfolioAllocationState,
    TradeAllocationInput,
    TransparentPortfolioEvaluator,
)


def trade(
    trade_id: str,
    *,
    netting_set_id: str | None = None,
    counterparty_id: str = "CP1",
    currency: str = "USD",
    product_family: str = "IR_SWAP",
    scale: float = 1.0,
    threshold: float = 0.0,
    mta: float = 0.0,
    concentration_group: str = "",
    stress_multiplier: float = 1.0,
) -> TradeAllocationInput:
    index = int(trade_id.lstrip("T") or 1)
    return TradeAllocationInput(
        trade_id=trade_id,
        counterparty_id=counterparty_id,
        netting_set_id=netting_set_id or f"NS{index}",
        currency=currency,
        product_family=product_family,
        scale=scale,
        standalone=AdjustmentVector(
            cva=5.0 + index,
            dva=0.8 + 0.1 * index,
            fca=1.5 + 0.2 * index,
            fba=0.2,
            mva=0.6 + 0.1 * index,
            kva=1.0 + 0.2 * index,
            wwr_uplift=0.1 * index,
            stress_adjustment=-0.05 * index,
        ),
        threshold=threshold,
        minimum_transfer_amount=mta,
        concentration_group=concentration_group,
        stress_multiplier=stress_multiplier,
    )


def additive_portfolio() -> PortfolioAllocationState:
    return PortfolioAllocationState(
        "P_ADD",
        (
            trade("T1"),
            trade("T2", counterparty_id="CP2", currency="EUR"),
            trade("T3", counterparty_id="CP3", product_family="OPTION"),
        ),
    )


def nonlinear_portfolio() -> PortfolioAllocationState:
    return PortfolioAllocationState(
        "P_NONLINEAR",
        (
            trade("T1", netting_set_id="NS1", threshold=100.0, mta=25.0, concentration_group="G1"),
            trade("T2", netting_set_id="NS1", concentration_group="G1"),
            trade("T3", counterparty_id="CP2", concentration_group="G2"),
        ),
        collateral_regime_switch=True,
        concentration_addon_rate=0.30,
    )


def evaluator() -> TransparentPortfolioEvaluator:
    return TransparentPortfolioEvaluator()
