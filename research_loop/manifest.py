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
    return {
        "run_id": run_id,
        "created_date": created_date,
        "parent_run": parent_run,
        "status": "PLAN_READY",
        "approval": {"plan_approved": False, "approved_at": None},
        "provenance": {
            "branch": None,
            "code_commit_sha": None,
            "command": None,
            "dataset": None,
            "split": None,
            "model_or_checkpoint": None,
            "seeds": [],
        },
        "artifacts": {"missing": []},
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
