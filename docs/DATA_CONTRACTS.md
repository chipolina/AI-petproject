# Data Contracts

## Failure Event (JSONL)

Each line in failures.jsonl represents a single test failure.

Required fields:
- run_id
- timestamp
- test_nodeid
- component (api | ui)
- env
- commit_sha
- error_type
- error_message
- stacktrace_raw
- stacktrace_clean
- artifacts (paths to screenshots/traces/allure)

## Embedding Input Text

Embedding text is composed as:

<component>
<error_message>
<top N lines of cleaned stacktrace>
<endpoint or page if available>

The goal is semantic similarity, not full error reconstruction.

## Cluster Explanation Output (LLM)

LLM must return strict JSON:

{
"summary": "...",
"likely_root_cause": "...",
"qa_next_steps": "...",
"confidence": 0.0-1.0,
"tags": ["infra", "flaky", "product"]
}
