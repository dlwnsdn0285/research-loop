from __future__ import annotations

import argparse
from collections.abc import Callable
import os
from typing import Any
from urllib.parse import urlparse

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.server.transport_security import TransportSecuritySettings
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from .auth import mcp_auth_kwargs
from .github_store import GitHubAPIError, GitHubConfig, GitHubStore
from .service import ResearchService


mcp = MCPServer("Research Loop", **mcp_auth_kwargs())
_service: ResearchService | None = None


def service() -> ResearchService:
    global _service
    if _service is None:
        _service = ResearchService(GitHubStore(GitHubConfig.from_env()))
    return _service


def tool_call(fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    try:
        return fn(*args, **kwargs)
    except (GitHubAPIError, RuntimeError, ValueError) as exc:
        raise ToolError(str(exc)) from exc


def _csv_env(name: str) -> list[str]:
    return [value.strip() for value in os.environ.get(name, "").split(",") if value.strip()]


def _transport_security(host: str, port: int) -> TransportSecuritySettings:
    public_url = os.environ.get("MCP_PUBLIC_URL", "").strip()
    if public_url:
        parsed = urlparse(public_url)
        if not parsed.hostname:
            raise RuntimeError("MCP_PUBLIC_URL must be an absolute http(s) URL")
        allowed_hosts = [parsed.hostname]
        if parsed.port:
            allowed_hosts.append(f"{parsed.hostname}:{parsed.port}")
        allowed_origins = [f"{parsed.scheme}://{parsed.netloc}"]
        allowed_origins.extend(_csv_env("MCP_ALLOWED_ORIGINS"))
    else:
        allowed_hosts = [f"{host}:{port}", f"{host}:*", "127.0.0.1:*", "localhost:*", "[::1]:*"]
        allowed_origins = ["http://127.0.0.1:*", "http://localhost:*", "http://[::1]:*"]
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=sorted(set(allowed_hosts)),
        allowed_origins=sorted(set(allowed_origins)),
    )


@mcp.custom_route("/healthz", methods=["GET"])
async def healthz(request: Request) -> Response:
    return JSONResponse({"status": "ok", "service": "research-mcp"})


@mcp.tool()
def get_research_status() -> dict:
    """Return deterministic research-loop state. No scientific interpretation is performed."""
    return tool_call(service().get_research_status)


@mcp.tool()
def get_latest_run(status: str) -> dict:
    """Find the newest run with an exact protocol status such as COMPLETED or RESULTS_READY."""
    return tool_call(service().get_latest_run, status)


@mcp.tool()
def load_planning_context() -> dict:
    """Load durable planning context plus the repository plan template. Combine both with the current chat before writing a plan."""
    def load() -> dict:
        context = service().load_planning_context()
        context["plan_template"] = service().store.get_text("templates/01_PLAN.md")
        return context
    return tool_call(load)


@mcp.tool()
def create_planned_run(name: str, plan: str, author: str, run_date: str | None = None) -> dict:
    """Persist a plan already authored in the current chat and create a PLAN_READY child run."""
    return tool_call(service().create_planned_run, name=name, plan=plan, author=author, run_date=run_date)


@mcp.tool()
def load_analysis_context() -> dict:
    """Load latest RESULTS_READY plan, raw summary, and artifact inventory for chat-side analysis."""
    return tool_call(service().load_analysis_context)


@mcp.tool()
def read_run_file(run_path: str, relative_path: str, start_line: int | None = None, end_line: int | None = None) -> dict:
    """Read a specific text artifact from a run, optionally by line range, to verify evidence on demand."""
    return tool_call(service().read_run_file, run_path, relative_path, start_line, end_line)


@mcp.tool()
def save_analysis(content: str, author: str, run_path: str | None = None) -> dict:
    """Persist chat-authored 03_ANALYSIS.md and transition RESULTS_READY -> ANALYZED."""
    return tool_call(service().save_analysis, content=content, author=author, run_path=run_path)


@mcp.tool()
def load_critique_context() -> dict:
    """Load latest ANALYZED run for an independent critic; includes analysis plus raw artifact inventory."""
    return tool_call(service().load_critique_context)


@mcp.tool()
def save_critique(content: str, author: str, run_path: str | None = None) -> dict:
    """Persist chat-authored 04_CRITIQUE.md and transition ANALYZED -> CRITIQUED with cross-model guard."""
    return tool_call(service().save_critique, content=content, author=author, run_path=run_path)


@mcp.tool()
def complete_run(run_path: str | None = None) -> dict:
    """Validate core completion invariants and transition CRITIQUED -> COMPLETED."""
    return tool_call(service().complete_run, run_path=run_path)


def main() -> None:
    default_port = int(os.environ.get("PORT", "8000"))
    parser = argparse.ArgumentParser(description="Research Loop MCP server")
    parser.add_argument("--transport", choices=["stdio", "streamable-http"], default="stdio")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=default_port)
    args = parser.parse_args()
    if args.transport == "stdio":
        mcp.run()
    else:
        mcp.run(
            transport="streamable-http",
            host=args.host,
            port=args.port,
            json_response=True,
            stateless_http=True,
            transport_security=_transport_security(args.host, args.port),
        )


if __name__ == "__main__":
    main()
