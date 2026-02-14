# AI Triage CI Gate – Project Context

This repository contains a PoC of an AI-assisted test failure triage system
integrated into CI pipelines.

## Core Idea
Not all test failures are equal.
The system reduces noise in CI by grouping similar failures, explaining them,
and blocking pipelines only for relevant, new, or critical issues.

## What this project IS
- A quality infrastructure PoC
- A data-driven CI gating system
- A learning project for Quality Engineering / DevEx roles

## What this project is NOT
- Not a machine learning research project
- Not a test generation system
- Not an autonomous bug-fixing AI

## High-level Pipeline
1. Run API and UI tests
2. Collect failure events in a unified JSONL format
3. Generate embeddings for failures
4. Cluster failures using DBSCAN
5. Generate LLM-based explanations per cluster (local via Ollama)
6. Apply quality gates (new / severity / non-flaky / non-infra)
7. Publish results via Allure + Markdown/HTML reports

## Constraints
- Python-first
- No paid SaaS
- Reproducible locally
- Deterministic where possible
- Explicit data formats over magic

## Coding Principles
- Explicit > implicit
- Data structures are more important than algorithms
- Every script should be runnable independently
- CI is a first-class user
