# Migration from v1.3.0 to v1.4.0

v1.4.0 extends the v1.3 XVA validation platform without rewriting or deleting the immutable v1.3.0 release evidence.

| Area | v1.3.0 | v1.4.0 |
|---|---|---|
| Portfolio input | XVA reference inputs | canonical portfolio snapshot, lineage, and validation contracts |
| Currency | primarily single-currency XVA | governed multi-currency exposure and collateral |
| Initial margin | outside the release core | transparent IM proxies and MVA |
| Capital | outside the release core | transparent public capital profiles and KVA |
| Contribution analytics | component attribution | trade insertion/removal, marginal analytics, Euler validity, and residuals |
| Operations | deterministic CI | dependency-aware recalculation, cache, checkpoint, chunking, and scale evidence |
| Lifecycle | XVA-focused monitoring | unified v1.4 challenge, stability, drift, remediation, and advisory GenAI governance |

The `v1.3.0` tag remains annotated and immutable. No v1.4 artifact is backported into the v1.3 release manifest.
