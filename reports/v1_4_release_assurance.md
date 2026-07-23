# v1.4 Release Assurance

## Pre-release assurance

- complete Gate 0–8 matrix;
- 708 collected tests;
- local Gate 8 through Gate 0 tests;
- memory-intensive FX remediation tests;
- complete remaining repository suite;
- pull-request CI;
- post-merge main CI;
- immutable annotated `v1.3.0` tag;
- explicit human `RELEASE` approval.

## Post-release assurance

- annotated `v1.4.0` tag points to the validated main commit;
- GitHub release exists and is neither draft nor prerelease;
- release notes disclose monitoring and model boundaries;
- Gate 8 assurance tests pass after publication;
- working tree remains clean;
- `v1.3.0` remains preserved.
