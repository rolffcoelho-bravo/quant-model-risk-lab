# XVA v1.3 Governed GenAI Validation Challenge

**Status:** `VALIDATED_PENDING_HUMAN_REVIEW`
**Live provider execution:** `False`
**Human review required:** `True`

## XVA-G8-001 — MONITORING

The release evidence is internally coherent, but the public calibration and legal-enforceability boundary must remain explicit.

**Recommended human action:** Publish with PASS_WITH_MONITORING and retain the non-production boundary.

Citations:
- `docs/xva_independent_challenger_and_promotion.md`
- `docs/validation_matrix.md`

## XVA-G8-002 — MONITORING

Credit and wrong-way-risk controls are validated as public methodology rather than institution-approved calibration.

**Recommended human action:** Require revalidation before any institution-specific use.

Citations:
- `configs/xva_promotion_contract.yml`
- `reports/xva_v1_3_validation_dashboard.json`

## XVA-G8-003 — INFORMATIONAL

The repository-level USD/BRL option quote benchmark remains open and is not converted into a pass by the XVA release.

**Recommended human action:** Preserve OPEN_NO_PUBLIC_QUOTE_DATA until dated auditable quote evidence exists.

Citations:
- `docs/validation_matrix.md`
