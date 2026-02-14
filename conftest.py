import json
import os
import pytest
import traceback
from datetime import datetime
from pathlib import Path

ARTIFACTS_DIR = Path("artifacts/raw")
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
FAILURES_FILE = ARTIFACTS_DIR / "failures.jsonl"


def pytest_addoption(parser):
    parser.addoption("--env", action="store", default="local")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.when != "call" or report.passed:
        return

    env = item.config.getoption("--env")

    failure_event = {
        "run_id": os.getenv("CI_PIPELINE_ID", "local-run"),
        "timestamp": datetime.utcnow().isoformat(),
        "test_nodeid": item.nodeid,
        "suite": item.module.__name__,
        "component": "api",  # в tests_ui будет "ui"
        "env": env,
        "commit_sha": os.getenv("CI_COMMIT_SHA", "local"),
        "error_type": report.longrepr.reprcrash.message.split(":")[0],
        "error_message": report.longrepr.reprcrash.message,
        "stacktrace_raw": str(report.longrepr),
        "stacktrace_clean": _clean_stacktrace(report.longrepr),
        "artifacts": {},
    }

    with FAILURES_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(failure_event, ensure_ascii=False) + "\n")


def _clean_stacktrace(longrepr, max_lines: int = 15) -> str:
    lines = str(longrepr).splitlines()
    filtered = [l for l in lines if "site-packages" not in l]
    return "\n".join(filtered[-max_lines:])
