# Continuous Integration Validation Policy

## Purpose

The GitHub Actions validation workflow provides independent repository-level execution evidence for every pull request and every change merged into `main`.

The workflow converts local test evidence into a visible GitHub status check.

## Workflow

Primary workflow:

`/.github/workflows/validation-ci.yml`

Triggers:

- pull requests targeting `main`
- pushes to `main`
- manual workflow dispatch

## Controlled environment

The workflow uses:

- GitHub-hosted Ubuntu runner
- Python 3.12
- dependency installation from `requirements.txt`
- pip dependency caching
- headless Matplotlib through the `Agg` backend
- deterministic Python hash seed
- single-thread numerical-library settings
- UTC timezone
- repository `src` directory on `PYTHONPATH`

## Validation sequence

The workflow performs:

1. repository checkout
2. Python environment setup
3. dependency installation
4. dependency import verification
5. Matplotlib backend verification
6. Python bytecode compilation
7. complete pytest execution
8. JUnit result publication as a workflow artifact

## Permissions

The workflow has read-only repository-content permission.

It does not receive an OpenAI API key and does not execute the governed GenAI provider call.

GenAI unit, schema and grounding tests remain part of the deterministic test suite, but provider execution requires a separate controlled human-approved run.

## Failure decision

Any dependency, compilation or pytest failure causes the workflow status check to fail.

A failed CI status must block discretionary merge approval until the failure is understood and remediated.

## Evidence retention

The pytest JUnit file is retained as a GitHub Actions artifact for fourteen days.

This artifact supplements repository evidence. It does not replace deterministic reports, model inventories, validation contracts or human-review records.

## Governance boundary

Passing CI demonstrates that the committed repository state executes successfully under the controlled workflow.

It does not constitute:

- production approval
- regulatory model approval
- market calibration evidence
- external-data freshness certification
- validation of credentials or provider availability