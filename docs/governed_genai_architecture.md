
# Governed GenAI Validation Architecture

## Purpose

The governed GenAI layer supports independent challenge and validation documentation without transferring model-approval authority to a language model.

Its objective is controlled assistance, not autonomous judgement.

## Permitted functions

GenAI may:

- review supplied validation evidence
- identify missing or inconsistent documentation
- challenge assumptions against the approved evidence package
- organize findings into a structured schema
- propose questions for a human validator
- improve traceability and consistency

## Prohibited functions

GenAI may not:

- approve a model for production
- close a validation finding
- invent market data
- replace deterministic calculations
- override failed tests
- certify regulatory compliance
- infer access to confidential systems or proprietary data
- make an undocumented decision outside supplied evidence

## Architecture

```text
Approved evidence
      â†“
Evidence-package builder
      â†“
Versioned validation instruction
      â†“
Structured provider request
      â†“
Schema and grounding controls
      â†“
Human-review artifact
      â†“
Human validation decision
```

## Evidence-package control

The evidence package is deterministic and limited to approved repository material.

Typical components include:

- model description
- model inputs and sources
- quantitative test results
- challenger outputs
- monitoring status
- lifecycle records
- documented model boundaries
- open validation gates

## Prompt governance

A governed prompt defines the validation objective, permitted evidence, prohibited conclusions, response schema, grounding expectations, escalation conditions, and mandatory human review.

Prompt changes are version-controlled and testable.

## Structured response

The response separates finding, evidence reference, severity, rationale, recommended human action, uncertainty, and unresolved questions.

Free-form provider prose is not treated as sufficient validation evidence.

## Traceability

Where implemented, the workflow records or hashes the evidence package, instruction version, provider metadata, structured response, run manifest, and human-review status.

## CI boundary

The GitHub Actions workflow does not receive a provider credential.

CI verifies schemas, parsers, grounding rules, evidence-package construction, prompt contracts, prohibited-action controls, and human-review requirements.

A live provider call is a separate controlled execution.

## Decision boundary

The final decision remains human.

A successful GenAI run means that the controlled assistance layer executed as designed. It does not mean that the underlying quantitative model is approved.

## Repository evidence

- [`configs/genai_validation_contract.json`](configs/genai_validation_contract.json)
- [`conftest.py`](conftest.py)
- [`data/genai/README.md`](data/genai/README.md)
- [`data/genai/inputs/fx_option_validation_evidence.json`](data/genai/inputs/fx_option_validation_evidence.json)
- [`data/genai/outputs/fx_option_validation_challenge.json`](data/genai/outputs/fx_option_validation_challenge.json)
- [`data/genai/outputs/fx_option_validation_human_review.json`](data/genai/outputs/fx_option_validation_human_review.json)
- [`data/genai/outputs/fx_option_validation_run_manifest.json`](data/genai/outputs/fx_option_validation_run_manifest.json)
- [`docs/genai_model_risk_framework.md`](docs/genai_model_risk_framework.md)
- [`prompts/genai/independent_validation_challenge_v1.md`](prompts/genai/independent_validation_challenge_v1.md)
- [`reports/genai/.gitkeep`](reports/genai/.gitkeep)
- [`reports/genai/fx_option_genai_human_review.md`](reports/genai/fx_option_genai_human_review.md)
- [`reports/genai/fx_option_genai_validation_challenge.md`](reports/genai/fx_option_genai_validation_challenge.md)
- [`requirements.txt`](requirements.txt)
- [`scripts/__pycache__/build_genai_evidence_input.cpython-312.pyc`](scripts/__pycache__/build_genai_evidence_input.cpython-312.pyc)
- [`scripts/__pycache__/run_genai_validation_challenge.cpython-312.pyc`](scripts/__pycache__/run_genai_validation_challenge.cpython-312.pyc)
- [`scripts/build_genai_evidence_input.py`](scripts/build_genai_evidence_input.py)
- [`scripts/run_genai_validation_challenge.py`](scripts/run_genai_validation_challenge.py)
- [`scripts/run_xva_validation.py`](scripts/run_xva_validation.py)
- [`src/qmrl/__pycache__/genai_client.cpython-312.pyc`](src/qmrl/__pycache__/genai_client.cpython-312.pyc)
- [`src/qmrl/__pycache__/genai_grounding.cpython-312.pyc`](src/qmrl/__pycache__/genai_grounding.cpython-312.pyc)
