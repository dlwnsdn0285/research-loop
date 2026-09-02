from __future__ import annotations

from pathlib import PurePosixPath
from typing import Any

ARTIFACT_METADATA_FIELDS = ("path", "type", "description")


def artifact_path(artifact: Any) -> str | None:
    """Return a normalized artifact path from either a legacy string or metadata mapping."""
    if isinstance(artifact, str):
        value = artifact.strip()
        return value or None
    if isinstance(artifact, dict):
        value = artifact.get("path")
        if isinstance(value, str):
            value = value.strip()
            return value or None
    return None


def normalize_artifact_inventory(artifacts: Any) -> list[dict[str, Any]]:
    """Normalize legacy and metadata-rich artifact entries for reasoning clients."""
    if not isinstance(artifacts, list):
        return []

    normalized: list[dict[str, Any]] = []
    for artifact in artifacts:
        if isinstance(artifact, str):
            normalized.append(
                {
                    "path": artifact.strip() or None,
                    "type": None,
                    "description": None,
                    "metadata_complete": False,
                    "legacy_entry": True,
                }
            )
            continue

        if isinstance(artifact, dict):
            item = dict(artifact)
            item.setdefault("path", None)
            item.setdefault("type", None)
            item.setdefault("description", None)
            item["metadata_complete"] = all(
                isinstance(item.get(field), str) and bool(item[field].strip())
                for field in ARTIFACT_METADATA_FIELDS
            )
            item["legacy_entry"] = False
            normalized.append(item)
            continue

        normalized.append(
            {
                "path": None,
                "type": None,
                "description": None,
                "metadata_complete": False,
                "legacy_entry": False,
                "invalid_entry_type": type(artifact).__name__,
            }
        )
    return normalized


def validate_artifact_inventory(artifacts: Any, schema_version: int = 1) -> list[str]:
    """Validate artifact registry shape while preserving schema-v1 compatibility."""
    errors: list[str] = []
    if not isinstance(artifacts, list):
        return ["files.raw_results.artifacts must be a list"]

    if schema_version >= 2 and not artifacts:
        errors.append("schema_version >= 2 requires at least one registered raw artifact")

    for index, artifact in enumerate(artifacts):
        prefix = f"files.raw_results.artifacts[{index}]"

        if schema_version >= 2:
            if not isinstance(artifact, dict):
                errors.append(f"{prefix} must be a mapping with path, type, and description")
                continue
            for field in ARTIFACT_METADATA_FIELDS:
                value = artifact.get(field)
                if not isinstance(value, str) or not value.strip():
                    errors.append(f"{prefix}.{field} must be a non-empty string")
        elif not isinstance(artifact, (str, dict)):
            errors.append(f"{prefix} must be a path string or metadata mapping")
            continue

        path = artifact_path(artifact)
        if not path:
            if schema_version < 2:
                errors.append(f"{prefix} is missing a valid path")
            continue

        parsed = PurePosixPath(path)
        if parsed.is_absolute() or ".." in parsed.parts:
            errors.append(f"{prefix}.path must be a safe run-relative path: {path}")

    return errors
