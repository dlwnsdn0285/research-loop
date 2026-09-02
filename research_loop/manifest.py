from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import yaml

VALID_STATES = [
    "PLANNING", "PLAN_READY", "PLAN_APPROVED", "RUNNING",
    "RESULTS_READY", "ANALYZED", "CRITIQUED", "COMPLETED",
]


def read_manifest(run_dir: Path) -> dict:
    path = run_dir / "00_MANIFEST.yaml"
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def write_manifest(run_dir: Path, data: dict) -> None:
    path = run_dir / "00_MANIFEST.yaml"
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)


def new_manifest(run_id: str, created_date: str, parent_run: str | None = None) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "schema_version": 2,
        "run_id": run_id,
        "name": run_id,
        "status": "PLAN_READY",
        "created_at": now,
        "updated_at": now,
        "parent_run": {"run_id": parent_run, "path": None},
        "files": {
            "plan": "01_PLAN.md",
            "raw_results": {"summary": "02_RESULTS_RAW.md", "artifacts": []},
            "analysis": "03_ANALYSIS.md",
            "critique": "04_CRITIQUE.md",
        },
        "experiment": {
            "code_commit_sha": None,
            "branch": None,
            "command": None,
            "dataset": None,
            "dataset_version": None,
            "split": None,
            "seeds": [],
        },
        "approval": {"plan_approved": False, "approved_at": None},
        "provenance": {
            "plan_author": None,
            "raw_author": "experiment_runner",
            "analysis_author": None,
            "critique_author": None,
            "analysis_at": None,
            "critique_at": None,
        },
        "notes": [],
    }
