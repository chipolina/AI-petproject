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
import hashlib
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import requests


CLUSTERS_PATH = Path("artifacts/triage/clusters.json")
OUTPUT_PATH = Path("artifacts/triage/clusters_explained.json")
LOG_PATH = Path("artifacts/triage/explain.log")

OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "llama3:latest"
DEFAULT_TEMPERATURE = 0
MAX_SAMPLES_PER_CLUSTER = 3


# ---------------- Logging ----------------

def log_event(payload: Dict):
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload["timestamp"] = datetime.utcnow().isoformat()
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


# ---------------- Prompt ----------------

def build_prompt(cluster: Dict) -> str:
    samples = cluster["events"][:MAX_SAMPLES_PER_CLUSTER]

    failure_blocks = []
    for e in samples:
        failure_blocks.append(
            f"""
Error Type: {e.get("error_type")}
Error Message: {e.get("error_message")}
"""
        )

    failures_text = "\n---\n".join(failure_blocks)

    return f"""
You are a senior quality engineer analyzing CI test failures.

Analyze the following failures from the same cluster:

{failures_text}

Return STRICT JSON only with this schema:

{{
  "root_cause_summary": "<short technical explanation>",
  "category": "<assertion_mismatch | infra_issue | flaky_test | unknown>",
  "is_infrastructure_issue": <true|false>,
  "confidence": <float 0.0-1.0>
}}

Do not include any text outside JSON.
"""


# ---------------- Ollama Call ----------------

def call_ollama(prompt: str, model: str, temperature: float) -> Dict:
    payload = {
        "model": model,
        "prompt": prompt,
        "temperature": temperature,
        "stream": False,
    }

    start = time.time()

    response = requests.post(OLLAMA_URL, json=payload, timeout=120)
    duration_ms = int((time.time() - start) * 1000)

    response.raise_for_status()

    raw_text = response.json().get("response", "").strip()

    return {
        "raw_text": raw_text,
        "duration_ms": duration_ms,
    }


# ---------------- JSON Parsing ----------------

def parse_llm_json(raw_text: str) -> Dict:
    try:
        parsed = json.loads(raw_text)
        return {"ok": True, "data": parsed}
    except Exception:
        return {"ok": False, "data": None}


# ---------------- Main ----------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--temperature", type=float, default=DEFAULT_TEMPERATURE)

    args = parser.parse_args()

    if not CLUSTERS_PATH.exists():
        print("clusters.json not found.")
        return

    with CLUSTERS_PATH.open("r", encoding="utf-8") as f:
        clusters_data = json.load(f)

    explained_clusters = []

    for cluster in clusters_data.get("clusters", []):
        cluster_id = cluster["cluster_id"]

        prompt = build_prompt(cluster)
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:12]

        log_event({
            "level": "INFO",
            "cluster_id": cluster_id,
            "event": "llm_request",
            "model": args.model,
            "temperature": args.temperature,
            "prompt_hash": prompt_hash,
        })

        try:
            result = call_ollama(prompt, args.model, args.temperature)

            parse_result = parse_llm_json(result["raw_text"])

            log_event({
                "level": "INFO",
                "cluster_id": cluster_id,
                "event": "llm_response",
                "duration_ms": result["duration_ms"],
                "parse_ok": parse_result["ok"],
            })

            cluster_copy = cluster.copy()

            if parse_result["ok"]:
                cluster_copy["llm_explanation"] = parse_result["data"]
            else:
                cluster_copy["llm_explanation"] = {
                    "error": "invalid_json_from_llm",
                    "raw_text": result["raw_text"],
                }

            explained_clusters.append(cluster_copy)

        except Exception as e:
            log_event({
                "level": "ERROR",
                "cluster_id": cluster_id,
                "event": "llm_error",
                "error": str(e),
            })

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "total_clusters": len(explained_clusters),
                "clusters": explained_clusters,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"Explained {len(explained_clusters)} clusters.")
    print(f"Output written to {OUTPUT_PATH}")
    print(f"Logs written to {LOG_PATH}")


if __name__ == "__main__":
    main()

