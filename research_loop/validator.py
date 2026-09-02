from __future__ import annotations

from pathlib import Path
from .artifacts import artifact_path, validate_artifact_inventory
from .config import load_config
from .manifest import VALID_STATES, read_manifest

BASE_FILES = ["00_MANIFEST.yaml", "01_PLAN.md"]
STATE_FILES = {
    "RESULTS_READY": ["02_RESULTS_RAW.md"],
    "ANALYZED": ["02_RESULTS_RAW.md", "03_ANALYSIS.md"],
    "CRITIQUED": ["02_RESULTS_RAW.md", "03_ANALYSIS.md", "04_CRITIQUE.md"],
    "COMPLETED": ["02_RESULTS_RAW.md", "03_ANALYSIS.md", "04_CRITIQUE.md"],
}


def validate_run(run_dir: Path, project_root: Path | None = None) -> list[str]:
    errors: list[str] = []
    for name in BASE_FILES:
        if not (run_dir / name).exists():
            errors.append(f"missing {name}")
    if errors:
        return errors

    manifest = read_manifest(run_dir)
    status = manifest.get("status")
    if status not in VALID_STATES:
        errors.append(f"invalid status: {status}")
        return errors

    required = []
    status_index = VALID_STATES.index(status)
    for threshold, files in STATE_FILES.items():
        if status_index >= VALID_STATES.index(threshold):
            required = files
    for name in required:
        if not (run_dir / name).exists():
            errors.append(f"status {status} requires {name}")

    if status_index >= VALID_STATES.index("RESULTS_READY"):
        root = project_root or run_dir.parents[2]
        cfg = load_config(root)
        for rel in cfg.get("raw_results", {}).get("required_artifacts", []):
            if not (run_dir / rel).exists():
                errors.append(f"missing required raw artifact: {rel}")

        files = manifest.get("files", {}) or {}
        raw = files.get("raw_results", {}) or {}
        artifacts = raw.get("artifacts", []) or []
        schema_version = manifest.get("schema_version", 1)
        try:
            schema_version = int(schema_version)
        except (TypeError, ValueError):
            errors.append(f"invalid schema_version: {schema_version}")
            schema_version = 1

        errors.extend(validate_artifact_inventory(artifacts, schema_version))
        for artifact in artifacts:
            path = artifact_path(artifact)
            if path and not (run_dir / path).exists():
                errors.append(f"missing registered raw artifact: {path}")
    return errors


def discover_runs(history_root: Path) -> list[Path]:
    if not history_root.exists():
        return []
    return sorted(p.parent for p in history_root.glob("*/*/00_MANIFEST.yaml"))
