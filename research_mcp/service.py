from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import os
from pathlib import PurePosixPath
import re
from typing import Any
from zoneinfo import ZoneInfo

import yaml

from .github_store import GitHubAPIError, GitHubStore

ALLOWED_STATUSES = [
    "PLANNING", "PLAN_READY", "PLAN_APPROVED", "RUNNING",
    "RESULTS_READY", "ANALYZED", "CRITIQUED", "COMPLETED",
]
ACTIVE_STATUSES = set(ALLOWED_STATUSES) - {"COMPLETED"}
ROOT = "research_runs_history"


def research_now() -> datetime:
    return datetime.now(ZoneInfo(os.environ.get("RESEARCH_TIMEZONE", "UTC")))


def now_iso() -> str:
    return research_now().isoformat(timespec="seconds")


def parse_yaml(text: str) -> dict[str, Any]:
    value = yaml.safe_load(text) or {}
    if not isinstance(value, dict):
        raise RuntimeError("Manifest must be a YAML mapping")
    return value


def dump_yaml(value: dict[str, Any]) -> str:
    return yaml.safe_dump(value, sort_keys=False, allow_unicode=True)


def slugify(name: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return value or "experiment"


def parse_ts(value: object) -> datetime:
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            pass
    return datetime.min.astimezone()


@dataclass
class RunRecord:
    path: str
    manifest: dict[str, Any]


class ResearchService:
    """Protocol-aware state manager. It never performs scientific reasoning."""

    def __init__(self, store: GitHubStore):
        self.store = store

    def _manifest(self, run_path: str) -> dict[str, Any]:
        return parse_yaml(self.store.get_text(f"{run_path}/00_MANIFEST.yaml"))

    def list_runs(self) -> list[RunRecord]:
        records: list[RunRecord] = []
        try:
            day_entries = self.store.list_dir(ROOT)
        except GitHubAPIError as exc:
            if " 404 " in str(exc):
                return []
            raise
        for day in day_entries:
            if day.get("type") != "dir" or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day.get("name", "")):
                continue
            for run in self.store.list_dir(f"{ROOT}/{day['name']}"):
                if run.get("type") != "dir" or not run.get("name", "").startswith("exp"):
                    continue
                path = f"{ROOT}/{day['name']}/{run['name']}"
                records.append(RunRecord(path, self._manifest(path)))
        records.sort(
            key=lambda record: (
                parse_ts(record.manifest.get("updated_at")),
                parse_ts(record.manifest.get("created_at")),
                record.path,
            ),
            reverse=True,
        )
        return records

    def latest_run(self, status: str | None = None) -> RunRecord:
        if status is not None and status not in ALLOWED_STATUSES:
            raise ValueError(f"Unknown status: {status}")
        for record in self.list_runs():
            if status is None or record.manifest.get("status") == status:
                return record
        raise RuntimeError(f"No research run found for status={status or 'ANY'}")

    @staticmethod
    def _run_summary(record: RunRecord) -> dict[str, Any]:
        manifest = record.manifest
        return {
            "run_id": manifest.get("run_id"),
            "name": manifest.get("name"),
            "status": manifest.get("status"),
            "path": record.path,
            "created_at": manifest.get("created_at"),
            "updated_at": manifest.get("updated_at"),
            "parent_run": manifest.get("parent_run"),
            "provenance": manifest.get("provenance"),
        }

    def get_research_status(self) -> dict[str, Any]:
        runs = self.list_runs()
        by_status: dict[str, dict[str, Any]] = {}
        for status in ALLOWED_STATUSES:
            match = next((r for r in runs if r.manifest.get("status") == status), None)
            if match:
                by_status[status] = self._run_summary(match)
        latest = self._run_summary(runs[0]) if runs else None
        active = [self._run_summary(r) for r in runs if r.manifest.get("status") in ACTIVE_STATUSES]
        if active:
            next_action = f"Continue active run in state {active[0]['status']}"
        elif latest and latest["status"] == "COMPLETED":
            next_action = "Planner needed: create the next PLAN_READY run from current chat + durable context"
        else:
            next_action = "Bootstrap planning needed: no completed run exists yet"
        return {"latest": latest, "active_runs": active, "latest_by_status": by_status, "next_protocol_action": next_action}

    def get_latest_run(self, status: str) -> dict[str, Any]:
        return self._run_summary(self.latest_run(status))

    def load_planning_context(self) -> dict[str, Any]:
        protocol = self.store.get_text("RESEARCH_PROTOCOL.md")
        try:
            parent = self.latest_run("COMPLETED")
        except RuntimeError:
            return {
                "usage": "Bootstrap mode: combine the protocol and plan template with the CURRENT CHAT. No completed parent run exists yet.",
                "protocol": protocol,
                "parent_run": None,
                "manifest": None,
                "analysis": None,
                "critique": None,
            }
        files = parent.manifest.get("files", {}) or {}
        return {
            "usage": "Combine this durable state with the CURRENT CHAT. The MCP does not replace conversation context or choose the next experiment.",
            "protocol": protocol,
            "parent_run": self._run_summary(parent),
            "manifest": parent.manifest,
            "analysis": self.store.get_text(f"{parent.path}/{files.get('analysis', '03_ANALYSIS.md')}"),
            "critique": self.store.get_text(f"{parent.path}/{files.get('critique', '04_CRITIQUE.md')}"),
        }

    def create_planned_run(self, name: str, plan: str, author: str, run_date: str | None = None) -> dict[str, Any]:
        if not plan.strip() or not author.strip():
            raise ValueError("plan and author must not be empty")
        active = [r for r in self.list_runs() if r.manifest.get("status") in ACTIVE_STATUSES]
        if active:
            raise RuntimeError(f"Refusing to create a new run while active run exists: {active[0].path} status={active[0].manifest.get('status')}")
        try:
            parent = self.latest_run("COMPLETED")
        except RuntimeError:
            parent = None
        day = run_date or research_now().date().isoformat()
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day):
            raise ValueError("run_date must be YYYY-MM-DD")
        try:
            entries = self.store.list_dir(f"{ROOT}/{day}")
        except GitHubAPIError as exc:
            if " 404 " not in str(exc):
                raise
            entries = []
        nums = []
        for entry in entries:
            match = re.match(r"exp(\d+)_", entry.get("name", ""))
            if entry.get("type") == "dir" and match:
                nums.append(int(match.group(1)))
        n = max(nums, default=0) + 1
        run_id = f"{day}_exp{n:02d}"
        run_path = f"{ROOT}/{day}/exp{n:02d}_{slugify(name)}"
        manifest = parse_yaml(self.store.get_text("templates/00_MANIFEST.yaml"))
        ts = now_iso()
        manifest.update({"run_id": run_id, "name": name, "status": "PLAN_READY", "created_at": ts, "updated_at": ts})
        manifest["parent_run"] = ({"run_id": parent.manifest.get("run_id"), "path": parent.path} if parent else {"run_id": None, "path": None})
        manifest.setdefault("provenance", {})["plan_author"] = author
        commit = self.store.commit_files(
            {f"{run_path}/00_MANIFEST.yaml": dump_yaml(manifest), f"{run_path}/01_PLAN.md": plan.rstrip() + "\n"},
            f"exp: add plan for {run_id}",
        )
        return {"run_id": run_id, "run_path": run_path, "status": "PLAN_READY", "commit_sha": commit}

    def _context_for(self, status: str, include_analysis: bool) -> dict[str, Any]:
        record = self.latest_run(status)
        files = record.manifest.get("files", {}) or {}
        raw = files.get("raw_results", {}) or {}
        result = {
            "usage": "Combine this durable state with the CURRENT CHAT. Read only raw artifacts needed to verify load-bearing claims using read_run_file().",
            "protocol": self.store.get_text("RESEARCH_PROTOCOL.md"),
            "run": self._run_summary(record),
            "manifest": record.manifest,
            "plan": self.store.get_text(f"{record.path}/{files.get('plan', '01_PLAN.md')}"),
            "raw_summary": self.store.get_text(f"{record.path}/{raw.get('summary', '02_RESULTS_RAW.md')}"),
            "raw_artifacts": raw.get("artifacts", []) or [],
        }
        if include_analysis:
            result["analysis"] = self.store.get_text(f"{record.path}/{files.get('analysis', '03_ANALYSIS.md')}")
        return result

    def load_analysis_context(self) -> dict[str, Any]:
        return self._context_for("RESULTS_READY", include_analysis=False)

    def load_critique_context(self) -> dict[str, Any]:
        return self._context_for("ANALYZED", include_analysis=True)

    def read_run_file(self, run_path: str, relative_path: str, start_line: int | None = None, end_line: int | None = None) -> dict[str, Any]:
        run = PurePosixPath(run_path)
        rel = PurePosixPath(relative_path)
        if run.is_absolute() or rel.is_absolute() or ".." in run.parts or ".." in rel.parts:
            raise ValueError("run_path and relative_path must be safe repository-relative paths")
        if not str(run).startswith(f"{ROOT}/"):
            raise ValueError(f"run_path must be under {ROOT}/")
        text = self.store.get_text(f"{run.as_posix()}/{rel.as_posix()}")
        lines = text.splitlines()
        first = 1 if start_line is None else start_line
        last = len(lines) if end_line is None else end_line
        if first < 1 or last < first:
            raise ValueError("Invalid line range")
        return {
            "run_path": run.as_posix(), "relative_path": rel.as_posix(), "start_line": first,
            "end_line": min(last, len(lines)), "total_lines": len(lines),
            "content": "\n".join(lines[first - 1:last]),
        }

    def save_analysis(self, content: str, author: str, run_path: str | None = None) -> dict[str, Any]:
        record = self._resolve_run(run_path, "RESULTS_READY")
        if record.manifest.get("status") != "RESULTS_READY":
            raise RuntimeError(f"Analysis requires RESULTS_READY, got {record.manifest.get('status')}")
        provenance = record.manifest.setdefault("provenance", {})
        if provenance.get("analysis_author"):
            raise RuntimeError("analysis_author already set; refusing overwrite")
        ts = now_iso()
        provenance.update({"analysis_author": author, "analysis_at": ts})
        record.manifest.update({"status": "ANALYZED", "updated_at": ts})
        analysis_name = record.manifest.get("files", {}).get("analysis", "03_ANALYSIS.md")
        commit = self.store.commit_files(
            {f"{record.path}/{analysis_name}": content.rstrip() + "\n", f"{record.path}/00_MANIFEST.yaml": dump_yaml(record.manifest)},
            f"analysis: add analysis for {record.manifest.get('run_id')}",
        )
        return {"run_path": record.path, "status": "ANALYZED", "commit_sha": commit}

    def save_critique(self, content: str, author: str, run_path: str | None = None) -> dict[str, Any]:
        record = self._resolve_run(run_path, "ANALYZED")
        provenance = record.manifest.setdefault("provenance", {})
        analysis_author = provenance.get("analysis_author")
        if record.manifest.get("status") != "ANALYZED":
            raise RuntimeError(f"Critique requires ANALYZED, got {record.manifest.get('status')}")
        if not analysis_author:
            raise RuntimeError("Missing analysis_author")
        if analysis_author == author:
            raise RuntimeError("Cross-model safeguard: critique_author must differ from analysis_author")
        if provenance.get("critique_author"):
            raise RuntimeError("critique_author already set; refusing overwrite")
        ts = now_iso()
        provenance.update({"critique_author": author, "critique_at": ts})
        record.manifest.update({"status": "CRITIQUED", "updated_at": ts})
        critique_name = record.manifest.get("files", {}).get("critique", "04_CRITIQUE.md")
        commit = self.store.commit_files(
            {f"{record.path}/{critique_name}": content.rstrip() + "\n", f"{record.path}/00_MANIFEST.yaml": dump_yaml(record.manifest)},
            f"analysis: add critique for {record.manifest.get('run_id')}",
        )
        return {"run_path": record.path, "status": "CRITIQUED", "commit_sha": commit}

    def complete_run(self, run_path: str | None = None) -> dict[str, Any]:
        record = self._resolve_run(run_path, "CRITIQUED")
        self._validate_for_completion(record)
        record.manifest.update({"status": "COMPLETED", "updated_at": now_iso()})
        commit = self.store.commit_files(
            {f"{record.path}/00_MANIFEST.yaml": dump_yaml(record.manifest)},
            f"exp: complete {record.manifest.get('run_id')}",
        )
        return {"run_path": record.path, "status": "COMPLETED", "commit_sha": commit}

    def _resolve_run(self, run_path: str | None, default_status: str) -> RunRecord:
        return RunRecord(run_path, self._manifest(run_path)) if run_path else self.latest_run(default_status)

    def _validate_for_completion(self, record: RunRecord) -> None:
        manifest = record.manifest
        provenance = manifest.get("provenance", {}) or {}
        if manifest.get("status") != "CRITIQUED":
            raise RuntimeError("Run must be CRITIQUED before completion")
        if not provenance.get("analysis_author") or not provenance.get("critique_author"):
            raise RuntimeError("Missing analysis/critique author provenance")
        if provenance.get("analysis_author") == provenance.get("critique_author"):
            raise RuntimeError("analysis_author and critique_author must differ")
        files = manifest.get("files", {}) or {}
        raw = files.get("raw_results", {}) or {}
        required = [files.get("plan", "01_PLAN.md"), raw.get("summary", "02_RESULTS_RAW.md"), files.get("analysis", "03_ANALYSIS.md"), files.get("critique", "04_CRITIQUE.md")]
        for relative in required:
            if not self.store.exists(f"{record.path}/{relative}"):
                raise RuntimeError(f"Missing required file: {relative}")
        artifacts = raw.get("artifacts", []) or []
        if not artifacts:
            raise RuntimeError("No raw artifacts registered in manifest files.raw_results.artifacts")
        for artifact in artifacts:
            path = artifact.get("path") if isinstance(artifact, dict) else artifact
            if not path or not self.store.exists(f"{record.path}/{path}"):
                raise RuntimeError(f"Missing registered raw artifact: {path}")
