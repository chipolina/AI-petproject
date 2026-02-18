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
import sys
from pathlib import Path


EXPLAINED_PATH = Path("artifacts/triage/clusters_explained.json")
BASELINE_PATH = Path("artifacts/baseline/baseline_clusters.json")
OUTPUT_PATH = Path("artifacts/triage/gate_result.json")


def load_json(path: Path):
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def extract_cluster_signature(cluster: dict) -> str:
    explanation = cluster.get("llm_explanation", {})
    return explanation.get("root_cause_summary", "")


def load_baseline_signatures():
    baseline = load_json(BASELINE_PATH)
    if not baseline:
        return set()

    return {
        extract_cluster_signature(c)
        for c in baseline.get("clusters", [])
    }


def should_fail(cluster: dict, baseline_signatures: set) -> bool:
    explanation = cluster.get("llm_explanation", {})
    signature = extract_cluster_signature(cluster)

    if signature in baseline_signatures:
        return False

    if explanation.get("is_infrastructure_issue") is True:
        return False

    if explanation.get("category") == "flaky_test":
        return False

    # Severity & component check (sample first event)
    sample_event = cluster.get("events", [])[0]
    severity = sample_event.get("severity", "medium")
    component = sample_event.get("component", "unknown")

    if severity == "high" and component == "api":
        return True

    return False


def main():
    explained = load_json(EXPLAINED_PATH)

    if not explained:
        print("clusters_explained.json not found.")
        sys.exit(1)

    baseline_signatures = load_baseline_signatures()

    failing_clusters = []

    for cluster in explained.get("clusters", []):
        if should_fail(cluster, baseline_signatures):
            failing_clusters.append(cluster)

    result = {
        "total_clusters": len(explained.get("clusters", [])),
        "failing_clusters": len(failing_clusters),
        "fail": len(failing_clusters) > 0,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(json.dumps(result, indent=2))

    if result["fail"]:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
