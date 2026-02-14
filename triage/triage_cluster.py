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

import json
from pathlib import Path
from typing import List, Dict

import numpy as np
from sklearn.cluster import DBSCAN


INPUT_PATH = Path("artifacts/triage/failures_with_vec.jsonl")
OUTPUT_PATH = Path("artifacts/triage/clusters.json")


def load_events(path: Path) -> List[Dict]:
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def cluster_embeddings(vectors: np.ndarray, eps: float = 0.3, min_samples: int = 1):
    model = DBSCAN(
        eps=eps,
        min_samples=min_samples,
        metric="cosine",
    )
    labels = model.fit_predict(vectors)
    return labels


def build_cluster_output(events: List[Dict], labels: List[int]) -> Dict:
    clusters = {}

    for event, label in zip(events, labels):
        label = int(label)
        clusters.setdefault(label, []).append(event)

    result = {
        "total_events": len(events),
        "total_clusters": len(clusters),
        "clusters": [],
    }

    for cluster_id, items in clusters.items():
        result["clusters"].append(
            {
                "cluster_id": cluster_id,
                "size": len(items),
                "sample_error_type": items[0]["error_type"],
                "sample_message": items[0]["error_message"],
                "events": items,
            }
        )

    return result


def main():
    events = load_events(INPUT_PATH)

    if not events:
        print("No embedded failures found.")
        return

    vectors = np.array([e["embedding"] for e in events])

    labels = cluster_embeddings(vectors)

    result = build_cluster_output(events, labels)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Clustered {result['total_events']} events.")
    print(f"Detected {result['total_clusters']} clusters.")
    print(f"Output written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
