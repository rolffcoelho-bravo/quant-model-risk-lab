# GenAI Independent Validation Challenge

Evidence package: `QMRL-GENAI-FXOPTION-002`
Provider: `openai`
API: `responses`
Model: `gpt-5-mini-2025-08-07`
Decision: **CONDITIONAL**
Grounding gate: **PASS**

## Executive summary

The package provides a reproducible Garman Kohlhagen implementation, end to end scripts, example outputs and basic tests. Key validation controls are present for parity, shock grids and lifecycle metadata but several governance and methodological gaps remain that require human review before using outputs for production pricing or risk-taking decisions.

## Supported use

Vanilla European USD/BRL option valuation review, scenario exploration and first order Greek checks within the documented limitations of the lognormal model.

## Prohibited use

Use for smile calibrated pricing, path dependent option valuation, automated trading decisions or regulatory capital without additional calibration and governance.

## Findings

### GENAI-001 | Put call parity pass tolerance is implemented but rationale is undocumented

- Severity: `medium`
- Category: `governance`
- Source: `scripts/run_fx_options_validation.py`
- Evidence: 'status': "PASS" if abs(parity_gap) <= 1e-6 * max(abs(call.premium_domestic), 1.0) else "REVIEW",
- Interpretation: A numeric tolerance is applied to label parity checks as pass but the repository does not provide a documented rationale or governance justification for that tolerance.
- Required action: Record the tolerance rationale in validation documentation and map the tolerance to risk appetite and numerical precision tests.

### GENAI-002 | Realised volatility estimator uses hard coded fallbacks and bounds

- Severity: `medium`
- Category: `methodology`
- Source: `scripts/run_fx_options_validation.py`
- Evidence: if len(returns) < 20:
        return 0.15
...
    return max(min(vol, 0.60), 0.05
- Interpretation: The volatility estimation function applies hard coded sample length fallbacks and upper and lower bounds without documented empirical justification in the package.
- Required action: Provide documented rationale for the fallback and bound choices and add sensitivity tests that show how outputs change when these defaults are varied.

### GENAI-003 | Volatility floor applied in surface generation is hard coded

- Severity: `low`
- Category: `implementation`
- Source: `src/qmrl/fx_options.py`
- Evidence: shocked_vol = max(float(base_volatility) + float(vol_shock), 0.01)
- Interpretation: The spot/vol surface generator imposes an absolute minimum volatility that is not explained in the validation report.
- Required action: Document why the volatility floor was chosen and include tests that demonstrate behaviour when the floor is reached.

### GENAI-004 | No market benchmark or challenger comparison for option prices and smile

- Severity: `high`
- Category: `validation`
- Source: `reports/fx_option_validation_report.md`
- Evidence: The validation evidence covers call and put values, Greeks, put-call parity, spot shocks, volatility shocks and model lifecycle controls.
- Interpretation: The report documents internal checks but does not include evidence comparing model prices to observable market option quotes or to a challenger model for the volatility smile.
- Required action: Include market price benchmarking and challenger model comparisons before using outputs for pricing decisions beyond exploratory validation.

### GENAI-005 | Apparent unit or strike inconsistency between spot and strike values

- Severity: `medium`
- Category: `data`
- Source: `reports/fx_option_validation_report.md`
- Evidence: | Spot USD/BRL | 4.990000 |
| Strike | 30.533850 |
- Interpretation: The base valuation table shows a strike value that is not on the same scale as the spot quote, creating an unresolved unit or mapping question for how strikes are represented.
- Required action: Clarify units and notional mapping for strike and spot in documentation and confirm that strike inputs align with pricing code expectations.

### GENAI-006 | Automated tests focus on artifact creation and basic sanity checks but do not enforce numerical reproducibility

- Severity: `medium`
- Category: `implementation`
- Source: `tests/test_fx_options_outputs.py`
- Evidence: assert Path("data/official/processed/fx_option_validation_summary.csv").exists()
- Interpretation: Tests confirm that scripts produce output files and basic positivity assertions exist but do not assert numerical regression tolerances or deterministic seeds for reproducible numerical outputs.
- Required action: Add unit tests that verify numerical reproducibility, edge cases and regression tolerances for key Greeks and prices.

### GENAI-007 | Lifecycle record lists monitoring triggers but no automated monitoring implementation is provided

- Severity: `low`
- Category: `monitoring`
- Source: `data/official/processed/fx_option_lifecycle_register.csv`
- Evidence: "monitoring_trigger": "spot move, realised volatility change, rate change, parity gap, delta/vega sign change"
- Interpretation: The lifecycle register defines sensible monitoring triggers but the package lacks code or configuration that implements those monitoring checks.
- Required action: Provide monitoring automation or an operational plan that connects lifecycle triggers to alerting and revalidation workflows.

## Missing evidence

- market price benchmarking for option prices and smile
- documented numerical tolerance and parity rationale
- documentation of volatility estimator choices and thresholds
- automated monitoring implementation tied to lifecycle triggers
- calibration and challenger model comparison evidence

## Deterministic grounding controls

- PASS: all citations resolve to supplied sources.
- PASS: no unsupported numeric claim was detected.
- PASS: the mandatory human-review gate is preserved.

## Governance statement

This GenAI output is challenger evidence only. It does not alter the deterministic pricing model, replace independent validation, or constitute formal model approval.
