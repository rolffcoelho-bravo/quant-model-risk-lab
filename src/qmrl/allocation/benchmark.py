"""Locked synthetic benchmarks for v1.4 Gate 5."""

from __future__ import annotations

from .attribution import build_attribution
from .challenger import challenge_leave_one_out
from .diagnostics import detect_nonlinearity
from .domain import AdjustmentVector, PortfolioAllocationState, TradeAllocationInput
from .euler import euler_allocation, leave_one_out_allocation
from .evaluator import TransparentPortfolioEvaluator
from .incremental import insert_trade, remove_trade
from .marginal import finite_difference_marginal


def reference_trades() -> tuple[TradeAllocationInput, ...]:
    return (
        TradeAllocationInput(
            trade_id="T1",
            counterparty_id="CP1",
            netting_set_id="NS1",
            currency="USD",
            product_family="IR_SWAP",
            scale=1.0,
            standalone=AdjustmentVector(
                cva=10.0, dva=2.0, fca=3.0, fba=0.5, mva=1.5, kva=2.5,
                wwr_uplift=0.4, stress_adjustment=-0.2,
            ),
            concentration_group="G1",
        ),
        TradeAllocationInput(
            trade_id="T2",
            counterparty_id="CP1",
            netting_set_id="NS1",
            currency="EUR",
            product_family="FX_FORWARD",
            scale=0.8,
            standalone=AdjustmentVector(
                cva=6.0, dva=1.0, fca=2.0, fba=0.3, mva=1.0, kva=1.7,
                wwr_uplift=0.2, stress_adjustment=-0.1,
            ),
            concentration_group="G1",
        ),
        TradeAllocationInput(
            trade_id="T3",
            counterparty_id="CP2",
            netting_set_id="NS2",
            currency="USD",
            product_family="OPTION",
            scale=1.2,
            standalone=AdjustmentVector(
                cva=7.0, dva=1.2, fca=1.5, fba=0.2, mva=0.8, kva=2.0,
                wwr_uplift=0.5, stress_adjustment=-0.4,
            ),
            concentration_group="G2",
        ),
    )


def additive_portfolio() -> PortfolioAllocationState:
    trades = reference_trades()
    # Separate netting sets remove the transparent netting interaction.
    additive = tuple(
        TradeAllocationInput(
            trade_id=trade.trade_id,
            counterparty_id=trade.counterparty_id,
            netting_set_id=f"ADD_{trade.trade_id}",
            currency=trade.currency,
            product_family=trade.product_family,
            scale=trade.scale,
            standalone=trade.standalone,
            concentration_group=trade.concentration_group,
        )
        for trade in trades
    )
    return PortfolioAllocationState("ADDITIVE", additive)


def nonlinear_portfolio() -> PortfolioAllocationState:
    trades = list(reference_trades())
    trades[0] = TradeAllocationInput(
        **{
            **trades[0].__dict__,
            "threshold": 100.0,
            "minimum_transfer_amount": 25.0,
        }
    )
    return PortfolioAllocationState(
        "NONLINEAR",
        tuple(trades),
        collateral_regime_switch=True,
        concentration_addon_rate=0.25,
    )


def run_gate5_benchmarks() -> dict[str, float | str | bool]:
    evaluator = TransparentPortfolioEvaluator()
    additive = additive_portfolio()
    nonlinear = nonlinear_portfolio()

    euler = euler_allocation(additive, evaluator)
    loo = leave_one_out_allocation(nonlinear, evaluator)
    marginal = finite_difference_marginal(additive, "T1", evaluator)
    inserted = TradeAllocationInput(
        trade_id="T4",
        counterparty_id="CP3",
        netting_set_id="NS4",
        currency="GBP",
        product_family="IR_SWAP",
        scale=0.5,
        standalone=AdjustmentVector(cva=2.0, fca=0.5, mva=0.2, kva=0.4),
    )
    insertion = insert_trade(additive, inserted, evaluator)
    removal = remove_trade(additive, "T1", evaluator)
    challenge = challenge_leave_one_out(additive, evaluator)
    attribution = build_attribution(nonlinear, loo)
    nonlinear_report = detect_nonlinearity(nonlinear, evaluator)

    return {
        "additive_euler_status": euler.status.value,
        "additive_euler_residual": euler.residual.total_adjustment,
        "nonlinear_euler_valid": nonlinear_report.euler_valid,
        "nonlinear_loo_residual": loo.residual.total_adjustment,
        "marginal_status": marginal.status.value,
        "marginal_approximation_error": float(marginal.approximation_error or 0.0),
        "insertion_total": insertion.increment.total_adjustment,
        "removal_total": removal.increment.total_adjustment,
        "challenger_status": challenge.status.value,
        "trade_concentration_hhi": attribution.concentration_hhi,
    }
