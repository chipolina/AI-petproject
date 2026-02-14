"""
Global pytest configuration for AI-assisted CI failure triage.

Responsibilities:
- Capture structured failure events
- Normalize stack traces
- Persist failure data into JSONL format
- Stay independent from API/UI-specific fixtures

Design principles:
- Append-only JSONL
- Stable schema
- Deterministic behavior
- CI-friendly
"""

import json
import os
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

import pytest


# --- Configuration ----------------------------------------------------------

ARTIFACTS_DIR = Path("artifacts/raw")
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

FAILURES_FILE = ARTIFACTS_DIR / "failures.jsonl"


# --- Pytest Options ---------------------------------------------------------

def pytest_addoption(parser):
    parser.addoption(
        "--env",
        action="store",
        default="local",
        help="Execution environment (local/staging/ci)"
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "component(name): mark test component (api/ui)"
    )
    config.addinivalue_line(
        "markers",
        "severity(level): mark test severity (low/medium/high)"
    )
    config.addinivalue_line(
        "markers",
        "flaky: mark test as flaky"
    )


# --- Failure Capture Hook ---------------------------------------------------

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.when != "call" or report.passed:
        return

    failure_event = _build_failure_event(item, report)
    _append_failure_event(failure_event)


# --- Internal Helpers -------------------------------------------------------

def _build_failure_event(item, report) -> Dict[str, Any]:
    env = item.config.getoption("--env")

    component = _get_marker_value(item, "component") or "unknown"
    severity = _get_marker_value(item, "severity") or "medium"
    is_flaky = bool(item.get_closest_marker("flaky"))

    error_type, error_message = _extract_error_info(report)
    stacktrace_raw = str(report.longrepr)
    stacktrace_clean = _clean_stacktrace(stacktrace_raw)

    return {
        "run_id": os.getenv("CI_PIPELINE_ID", "local-run"),
        "timestamp": datetime.utcnow().isoformat(),
        "test_nodeid": item.nodeid,
        "suite": item.module.__name__,
        "component": component,
        "severity": severity,
        "is_flaky": is_flaky,
        "env": env,
        "commit_sha": os.getenv("CI_COMMIT_SHA", "local"),
        "error_type": error_type,
        "error_message": error_message,
        "stacktrace_raw": stacktrace_raw,
        "stacktrace_clean": stacktrace_clean,
        "artifacts": {},  # UI tests can extend this later
    }


def _get_marker_value(item, marker_name: str):
    marker = item.get_closest_marker(marker_name)
    if marker and marker.args:
        return marker.args[0]
    return None


def _extract_error_info(report):
    try:
        message = report.longrepr.reprcrash.message
        error_type = message.split(":")[0]
        return error_type, message
    except Exception:
        return "UnknownError", str(report.longrepr)


def _clean_stacktrace(stacktrace: str, max_lines: int = 20) -> str:
    lines = stacktrace.splitlines()

    filtered = [
        line
        for line in lines
        if "site-packages" not in line
    ]

    return "\n".join(filtered[-max_lines:])


def _append_failure_event(event: Dict[str, Any]):
    with FAILURES_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
