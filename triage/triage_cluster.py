"""
Purpose:
    This script is part of the AI-assisted CI failure triage pipeline.

Responsibilities:
    - Read structured failure events from JSONL
    - Perform a single, isolated transformation step
    - Write results to artifacts/triage

Context:
    - This script is executed inside CI
    - It must be deterministic and reproducible
    - It must not depend on pytest or test runtime state

Non-goals:
    - No ML model training
    - No external SaaS
    - No business logic inference
"""
