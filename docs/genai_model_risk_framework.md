# GenAI Model-Risk Framework

## Purpose

This layer demonstrates governed use of generative artificial intelligence inside an existing quantitative model-risk repository. The first use case is an independent challenge of the FX option validation evidence already produced by the deterministic Python workflow.

GenAI does not price the instrument, calculate Greeks, alter validation metrics or approve the model. It reads a controlled public evidence package and returns structured challenger findings.

## Architecture

```text
Existing deterministic validation evidence
                |
                v
Deterministic evidence-package builder
                |
                v
Versioned prompt + structured output schema
                |
                v
OpenAI Responses API
                |
                v
Structured validation challenge
                |
                v
Citation, number and human-review controls
                |
                v
Response JSON + run manifest + review report
```

## Public evidence

The layer records:

1. the exact prompt version
2. the structured response schema
3. hashes of every input file
4. the prompt hash
5. the model and provider response identifier
6. token-usage metadata when available
7. deterministic grounding results
8. the response hash
9. automated schema and grounding tests
10. the mandatory human-review boundary

## Model-use boundary

Allowed use:

- challenge documentation and assumptions
- identify missing validation evidence
- propose review actions
- summarize supplied evidence
- support human model-risk review

Prohibited use:

- change deterministic results
- approve or reject a production model without human review
- invent evidence
- make customer-level decisions
- process confidential or personally identifiable data
- claim regulatory validation

## First validation gate

The first gate passes only when:

- all tests pass
- all findings cite supplied source paths
- no unsupported numeric claim is detected
- the response preserves the human-review requirement
- the output and run manifest are saved
- a human reviews the generated report before commit