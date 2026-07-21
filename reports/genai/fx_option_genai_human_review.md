# Human Review of GenAI Validation Challenge

Review ID: QMRL-GENAI-HUMAN-REVIEW-001

Reviewed at UTC: 2026-07-21T23:03:32.8545780Z

Reviewer: Rodolfo Pereira

Evidence package: QMRL-GENAI-FXOPTION-002

Model: gpt-5-mini-2025-08-07

Provider response: resp_0e938f48f7e92763006a5fea403b6081a1b56a366c4382babc

GenAI decision: CONDITIONAL

Grounding gate: PASS

## Human-review decision

**ACCEPTED AS GOVERNED CHALLENGER EVIDENCE**

The structured GenAI response passed the deterministic grounding controls. Its citations resolve to supplied repository evidence, unsupported numerical claims were not detected, and the mandatory human-review boundary was preserved.

The challenger output is accepted as evidence of a governed GenAI-assisted model-risk workflow. It is not accepted as production approval and does not modify any deterministic pricing, risk or validation result.

## Model-use decision

Production approval: **NO**

Deterministic model result changed: **NO**

Human review completed: **YES**

Findings retained: **YES**

The current model-use decision remains conditional. Broader use requires closure or formal acceptance of the relevant validation, methodology, data, implementation, monitoring and governance findings.

## Finding disposition

- GENAI-001 | MEDIUM | Put call parity pass tolerance is implemented but rationale is undocumented | Disposition: OPEN
- GENAI-002 | MEDIUM | Realised volatility estimator uses hard coded fallbacks and bounds | Disposition: OPEN
- GENAI-003 | LOW | Volatility floor applied in surface generation is hard coded | Disposition: OPEN
- GENAI-004 | HIGH | No market benchmark or challenger comparison for option prices and smile | Disposition: OPEN
- GENAI-005 | MEDIUM | Apparent unit or strike inconsistency between spot and strike values | Disposition: OPEN
- GENAI-006 | MEDIUM | Automated tests focus on artifact creation and basic sanity checks but do not enforce numerical reproducibility | Disposition: OPEN
- GENAI-007 | LOW | Lifecycle record lists monitoring triggers but no automated monitoring implementation is provided | Disposition: OPEN

## Missing evidence retained for remediation

- market price benchmarking for option prices and smile
- documented numerical tolerance and parity rationale
- documentation of volatility estimator choices and thresholds
- automated monitoring implementation tied to lifecycle triggers
- calibration and challenger model comparison evidence

## Priority interpretation

The absence of a market benchmark or independent challenger comparison remains the most important validation gap.

The apparent strike and spot scale discrepancy must be investigated deterministically against the input construction, pricing contract and generated evidence before any interpretation is accepted.

The remaining findings should be converted into traceable remediation tasks with owners, evidence requirements and closure criteria.

## Governance conclusion

The GenAI layer has demonstrated:

- controlled evidence ingestion
- structured-output enforcement
- deterministic citation validation
- deterministic numerical grounding
- explicit model-use boundaries
- API and model traceability
- human review before acceptance
- separation between challenger analysis and model approval

This review accepts the GenAI output as auditable challenger evidence only. Human model-risk judgment remains the final authority.