from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any

import jwt
from jwt import PyJWKClient
from jwt.exceptions import PyJWTError, PyJWKClientError
from mcp.server.auth.provider import AccessToken, TokenVerifier
from mcp.server.auth.settings import AuthSettings
from pydantic import AnyHttpUrl


def _enabled(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _csv(name: str) -> tuple[str, ...]:
    raw = os.environ.get(name, "")
    return tuple(value.strip() for value in raw.split(",") if value.strip())


@dataclass(frozen=True)
class OAuthConfig:
    issuer_url: str
    resource_server_url: str
    audience: str
    jwks_url: str
    required_scopes: tuple[str, ...]
    allowed_subjects: frozenset[str]
    algorithms: tuple[str, ...]

    @classmethod
    def from_env(cls) -> "OAuthConfig | None":
        if not _enabled("MCP_AUTH_ENABLED"):
            return None

        issuer = os.environ.get("MCP_AUTH_ISSUER_URL", "").strip()
        resource = os.environ.get("MCP_PUBLIC_URL", "").strip()
        audience = os.environ.get("MCP_AUTH_AUDIENCE", "").strip()
        jwks_url = os.environ.get("MCP_AUTH_JWKS_URL", "").strip()
        if not issuer or not resource or not audience or not jwks_url:
            raise RuntimeError(
                "MCP_AUTH_ENABLED=true requires MCP_AUTH_ISSUER_URL, MCP_PUBLIC_URL, "
                "MCP_AUTH_AUDIENCE, and MCP_AUTH_JWKS_URL"
            )

        scopes = _csv("MCP_REQUIRED_SCOPES") or ("research:mcp",)
        algorithms = _csv("MCP_AUTH_ALGORITHMS") or ("RS256",)
        return cls(
            issuer_url=issuer,
            resource_server_url=resource,
            audience=audience,
            jwks_url=jwks_url,
            required_scopes=scopes,
            allowed_subjects=frozenset(_csv("MCP_ALLOWED_SUBJECTS")),
            algorithms=algorithms,
        )


class OIDCJWTTokenVerifier(TokenVerifier):
    """Verify JWT access tokens issued by an external OAuth/OIDC authorization server."""

    def __init__(self, config: OAuthConfig):
        self.config = config
        self.jwks = PyJWKClient(config.jwks_url)

    @staticmethod
    def _scopes(claims: dict[str, Any]) -> list[str]:
        raw = claims.get("scope")
        if isinstance(raw, str):
            scopes = raw.split()
        elif isinstance(raw, list):
            scopes = [str(value) for value in raw]
        else:
            scopes = []

        permissions = claims.get("permissions")
        if isinstance(permissions, list):
            for value in permissions:
                scope = str(value)
                if scope not in scopes:
                    scopes.append(scope)
        return scopes

    async def verify_token(self, token: str) -> AccessToken | None:
        try:
            signing_key = self.jwks.get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=list(self.config.algorithms),
                audience=self.config.audience,
                issuer=self.config.issuer_url,
                options={"require": ["exp", "sub", "iss", "aud"]},
            )
        except (PyJWTError, PyJWKClientError, ValueError):
            return None

        subject = str(claims.get("sub", ""))
        if not subject:
            return None
        if self.config.allowed_subjects and subject not in self.config.allowed_subjects:
            return None

        client_id = str(claims.get("azp") or claims.get("client_id") or "oauth-client")
        expires_at = claims.get("exp")
        return AccessToken(
            token=token,
            client_id=client_id,
            scopes=self._scopes(claims),
            expires_at=int(expires_at) if expires_at is not None else None,
            resource=self.config.resource_server_url,
            subject=subject,
            claims=claims,
        )


def mcp_auth_kwargs() -> dict[str, Any]:
    """Return MCPServer auth kwargs, or no auth kwargs for local/stdio use."""
    config = OAuthConfig.from_env()
    if config is None:
        return {}
    return {
        "token_verifier": OIDCJWTTokenVerifier(config),
        "auth": AuthSettings(
            issuer_url=AnyHttpUrl(config.issuer_url),
            resource_server_url=AnyHttpUrl(config.resource_server_url),
            required_scopes=list(config.required_scopes),
        ),
    }
