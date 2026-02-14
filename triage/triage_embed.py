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


import argparse
import json
from pathlib import Path
from typing import List, Dict

from sentence_transformers import SentenceTransformer


RAW_PATH = Path("artifacts/raw/failures.jsonl")
OUT_DIR = Path("artifacts/triage")
OUT_PATH = OUT_DIR / "failures_with_vec.jsonl"

DEFAULT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_STRATEGY = "semantic"


def load_failures(path: Path) -> List[Dict]:
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def build_embedding_input(event: Dict, strategy: str) -> str:
    error_type = event.get("error_type", "")
    error_message = event.get("error_message", "")
    stacktrace_clean = event.get("stacktrace_clean", "")
    stacktrace_raw = event.get("stacktrace_raw", "")

    if strategy == "semantic":
        return f"{error_type}\n{error_message}"

    if strategy == "semantic+stack":
        return f"{error_type}\n{error_message}\n\n{stacktrace_clean}"

    if strategy == "full":
        return (
            f"{error_type}\n"
            f"{error_message}\n\n"
            f"{stacktrace_clean}\n\n"
            f"{stacktrace_raw}"
        )

    raise ValueError(f"Unknown strategy: {strategy}")



def write_with_vectors(events: List[Dict], vectors: List[List[float]], strategy: str):
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with OUT_PATH.open("w", encoding="utf-8") as f:
        for event, vec in zip(events, vectors):
            event_with_vec = event.copy()
            event_with_vec["embedding"] = vec
            event_with_vec["embedding_strategy"] = strategy
            f.write(json.dumps(event_with_vec, ensure_ascii=False) + "\n")


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL_NAME,
        help="Embedding model name",
    )

    parser.add_argument(
        "--strategy",
        default=DEFAULT_STRATEGY,
        choices=["semantic", "semantic+stack", "full"],
        help="Embedding input strategy",
    )

    args = parser.parse_args()

    events = load_failures(RAW_PATH)

    if not events:
        print("No failure events found.")
        return

    texts = [build_embedding_input(e, args.strategy) for e in events]

    model = SentenceTransformer(args.model)
    vectors = model.encode(texts, normalize_embeddings=True).tolist()

    write_with_vectors(events, vectors, args.strategy)

    print(f"Embedded {len(events)} failure events.")
    print(f"Strategy used: {args.strategy}")
    print(f"Output written to {OUT_PATH}")




if __name__ == "__main__":
    main()
