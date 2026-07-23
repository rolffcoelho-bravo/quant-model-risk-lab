# v1.4 Model Boundaries and Governance

The v1.4 release is public research software and a model-risk evidence package.

## Enforced boundaries

- initial margin is labelled `PUBLIC_PROXY_NOT_SIMM_OR_CCP`;
- capital is labelled `PUBLIC_CAPITAL_PROXY_NOT_REGULATORY_APPROVAL`;
- MVA remains separate from FVA;
- full revaluation remains authoritative for incremental analytics;
- approximate marginal results disclose convergence and full-revaluation error;
- operational optimizations must preserve quantitative equivalence;
- GenAI is advisory only and cannot approve models, change quantitative results, close material findings, or promote releases;
- CI success demonstrates reproducibility, not production approval;
- production approval and regulatory approval remain false.
