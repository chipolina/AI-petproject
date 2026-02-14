# Architecture Overview

## Main Components

/tests_api
/tests_ui
Automated tests (pytest / Playwright)

/artifacts/raw
Raw failure events (JSONL)

/artifacts/triage
Derived triage data:
- embeddings
- clusters
- explanations

/triage
Standalone scripts:
- triage_embed.py
- triage_cluster.py
- triage_explain.py
- triage_gate.py

/reports
Human-readable outputs:
- report.md
- charts
- HTML exports

## Data Flow
Tests → Failure Events → Embeddings → Clusters → Explanations → Gate Decision → Report

## Important Design Rules
- Triage scripts do NOT depend on pytest internals
- JSONL is the source of truth
- CI must be able to run triage without UI or DB access
- All outputs must be reproducible from artifacts
