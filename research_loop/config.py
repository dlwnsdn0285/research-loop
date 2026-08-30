from __future__ import annotations

from pathlib import Path
import yaml

DEFAULT_CONFIG = {
    "history_root": "research_runs_history",
    "approval": {"before_plan_commit": True, "before_execution": True},
    "raw_results": {
        "immutable_after_results_ready": True,
        "required_artifacts": ["raw/config.yaml", "raw/metrics.json", "raw/stdout.log"],
    },
    "reasoning": {"policy": "none", "mode": "full"},
}


def load_config(project_root: Path) -> dict:
    path = project_root / "research-loop.yaml"
    if not path.exists():
        return DEFAULT_CONFIG.copy()
    with path.open("r", encoding="utf-8") as f:
        user = yaml.safe_load(f) or {}
    cfg = DEFAULT_CONFIG.copy()
    for key, value in user.items():
        if isinstance(value, dict) and isinstance(cfg.get(key), dict):
            cfg[key] = {**cfg[key], **value}
        else:
            cfg[key] = value
    return cfg
