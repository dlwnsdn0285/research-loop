from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen


class GitHubAPIError(RuntimeError):
    pass


@dataclass(frozen=True)
class GitHubConfig:
    repository: str
    token: str
    branch: str = "main"
    api_url: str = "https://api.github.com"

    @classmethod
    def from_env(cls) -> "GitHubConfig":
        repository = os.environ.get("RESEARCH_GITHUB_REPO", "").strip()
        token = os.environ.get("GITHUB_TOKEN", "").strip()
        if not repository or "/" not in repository:
            raise RuntimeError("RESEARCH_GITHUB_REPO must be set to owner/repo")
        if not token:
            raise RuntimeError("GITHUB_TOKEN is required")
        return cls(
            repository=repository,
            token=token,
            branch=os.environ.get("RESEARCH_GITHUB_BRANCH", "main").strip() or "main",
            api_url=os.environ.get("GITHUB_API_URL", "https://api.github.com").rstrip("/"),
        )


class GitHubStore:
    """Small GitHub REST wrapper used as the durable research-state backend."""

    def __init__(self, config: GitHubConfig):
        self.config = config

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> Any:
        url = f"{self.config.api_url}{path}"
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        request = Request(
            url,
            data=body,
            method=method,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.config.token}",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "research-loop-mcp",
                **({"Content-Type": "application/json"} if body is not None else {}),
            },
        )
        try:
            with urlopen(request, timeout=30) as response:
                raw = response.read()
                return json.loads(raw.decode("utf-8")) if raw else None
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise GitHubAPIError(f"GitHub API {method} {path} failed: {exc.code} {detail}") from exc

    def _repo_path(self, suffix: str) -> str:
        return f"/repos/{self.config.repository}{suffix}"

    def get_text(self, path: str) -> str:
        encoded_path = quote(path.strip("/"), safe="/")
        data = self._request(
            "GET",
            self._repo_path(f"/contents/{encoded_path}?ref={quote(self.config.branch, safe='')}")
        )
        if not isinstance(data, dict) or data.get("type") != "file":
            raise GitHubAPIError(f"Not a file: {path}")
        content = data.get("content", "")
        if data.get("encoding") == "base64" and content:
            return base64.b64decode(content).decode("utf-8")
        sha = data.get("sha")
        if not sha:
            raise GitHubAPIError(f"Missing blob sha for {path}")
        blob = self._request("GET", self._repo_path(f"/git/blobs/{sha}"))
        if blob.get("encoding") != "base64":
            raise GitHubAPIError(f"Unsupported blob encoding for {path}: {blob.get('encoding')}")
        return base64.b64decode(blob.get("content", "")).decode("utf-8")

    def exists(self, path: str) -> bool:
        try:
            self.get_text(path)
            return True
        except GitHubAPIError as exc:
            if " 404 " in str(exc):
                return False
            raise

    def list_dir(self, path: str) -> list[dict[str, Any]]:
        encoded_path = quote(path.strip("/"), safe="/")
        suffix = f"/contents/{encoded_path}" if encoded_path else "/contents"
        data = self._request(
            "GET",
            self._repo_path(f"{suffix}?ref={quote(self.config.branch, safe='')}")
        )
        if not isinstance(data, list):
            raise GitHubAPIError(f"Not a directory: {path}")
        return data

    def commit_files(self, files: dict[str, str], message: str) -> str:
        """Atomically commit multiple UTF-8 text files to the configured branch."""
        if not files:
            raise ValueError("files must not be empty")
        owner_repo = self.config.repository
        branch_q = quote(self.config.branch, safe="")
        head = self._request("GET", f"/repos/{owner_repo}/git/ref/heads/{branch_q}")
        parent_sha = head["object"]["sha"]
        parent_commit = self._request("GET", f"/repos/{owner_repo}/git/commits/{parent_sha}")
        base_tree = parent_commit["tree"]["sha"]

        entries: list[dict[str, str]] = []
        for path, content in files.items():
            blob = self._request(
                "POST",
                f"/repos/{owner_repo}/git/blobs",
                {"content": content, "encoding": "utf-8"},
            )
            entries.append({
                "path": path.strip("/"),
                "mode": "100644",
                "type": "blob",
                "sha": blob["sha"],
            })

        tree = self._request(
            "POST",
            f"/repos/{owner_repo}/git/trees",
            {"base_tree": base_tree, "tree": entries},
        )
        commit = self._request(
            "POST",
            f"/repos/{owner_repo}/git/commits",
            {"message": message, "tree": tree["sha"], "parents": [parent_sha]},
        )
        self._request(
            "PATCH",
            f"/repos/{owner_repo}/git/refs/heads/{branch_q}",
            {"sha": commit["sha"], "force": False},
        )
        return commit["sha"]
