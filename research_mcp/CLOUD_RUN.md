# Research MCP on Google Cloud Run

This guide deploys Research MCP as a lightweight remote protocol/state service. The lab or GPU machine remains separate and continues to execute experiments through git pull/push.

## Architecture

```text
ChatGPT / Claude
      │ HTTPS + OAuth bearer token
      ▼
Google Cloud Run
  Research MCP
  min instances = 0
  max instances = 1
      │ repo-scoped GitHub credential
      ▼
GitHub research repository
      ▲
      │ git pull / push
Coding Agent / lab server
```

## Security model

Use three independent protections:

1. HTTPS from Cloud Run for transport security.
2. OAuth/OIDC at the MCP application layer. `MCP_AUTH_ENABLED=true` makes the server validate JWT access tokens against an external issuer/JWKS endpoint, audience, required scopes, and optional subject allowlist.
3. A narrowly scoped GitHub credential that can access only the research repository the MCP manages.

Do not expose the service publicly while `MCP_AUTH_ENABLED=false`.

## 1. Prerequisites

Install and authenticate `gcloud`, then choose a project and region:

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud config set run/region YOUR_REGION
```

Enable required APIs:

```bash
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com
```

## 2. Create a runtime identity and GitHub secret

Create a dedicated runtime service account:

```bash
gcloud iam service-accounts create research-mcp-runtime \
  --display-name='Research MCP runtime'
```

Create a fine-grained GitHub token restricted to your research repository with repository Contents read/write permission. Store it in Secret Manager rather than source code or Docker build args:

```bash
printf '%s' 'YOUR_GITHUB_FINE_GRAINED_PAT' | \
  gcloud secrets create research-mcp-github-token --data-file=-
```

If the secret already exists:

```bash
printf '%s' 'YOUR_GITHUB_FINE_GRAINED_PAT' | \
  gcloud secrets versions add research-mcp-github-token --data-file=-
```

Grant the runtime identity access to that secret:

```bash
gcloud secrets add-iam-policy-binding research-mcp-github-token \
  --member='serviceAccount:research-mcp-runtime@YOUR_PROJECT_ID.iam.gserviceaccount.com' \
  --role='roles/secretmanager.secretAccessor'
```

## 3. Build the container

Create an Artifact Registry repository once:

```bash
gcloud artifacts repositories create research-mcp \
  --repository-format=docker \
  --location=YOUR_REGION
```

Build using the checked-in `cloudbuild.research-mcp.yaml`:

```bash
gcloud builds submit \
  --config cloudbuild.research-mcp.yaml \
  --substitutions=_IMAGE=YOUR_REGION-docker.pkg.dev/YOUR_PROJECT_ID/research-mcp/research-mcp:latest \
  .
```

The image contains only the protocol/MCP package and templates. It intentionally excludes models, datasets, checkpoints, and experiment outputs.

## 4. Bootstrap the Cloud Run URL privately

First deploy with Cloud Run IAM still blocking unauthenticated internet access and MCP OAuth disabled. This gives you the stable service URL without exposing an unauthenticated write-capable endpoint:

```bash
gcloud run deploy research-mcp \
  --image YOUR_REGION-docker.pkg.dev/YOUR_PROJECT_ID/research-mcp/research-mcp:latest \
  --service-account research-mcp-runtime@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --no-allow-unauthenticated \
  --min-instances 0 \
  --max-instances 1 \
  --cpu 1 \
  --memory 512Mi \
  --concurrency 8 \
  --set-env-vars RESEARCH_GITHUB_REPO=YOUR_GITHUB_USER/YOUR_RESEARCH_REPO,RESEARCH_GITHUB_BRANCH=main,RESEARCH_TIMEZONE=UTC,MCP_AUTH_ENABLED=false \
  --set-secrets GITHUB_TOKEN=research-mcp-github-token:latest
```

Retrieve the URL:

```bash
gcloud run services describe research-mcp \
  --format='value(status.url)'
```

The MCP endpoint is `<service-url>/mcp`; liveness is `<service-url>/healthz`.

## 5. Configure OAuth/OIDC

Use an external authorization server that issues JWT access tokens and exposes a JWKS endpoint. Configure the MCP resource/audience, normally the full MCP resource URL, for example:

```text
https://YOUR_CLOUD_RUN_HOST/mcp
```

Recommended token policy:

- asymmetric signing such as RS256;
- short-lived access tokens;
- audience exactly matching `MCP_AUTH_AUDIENCE`;
- required scope `research:mcp`;
- optional subject restriction via `MCP_ALLOWED_SUBJECTS`.

Research MCP is a resource server only. It does not store passwords or mint access tokens.

## 6. Enable application OAuth, then network access

Update the service with OAuth enabled:

```bash
gcloud run services update research-mcp \
  --set-env-vars RESEARCH_GITHUB_REPO=YOUR_GITHUB_USER/YOUR_RESEARCH_REPO,RESEARCH_GITHUB_BRANCH=main,RESEARCH_TIMEZONE=UTC,MCP_AUTH_ENABLED=true,MCP_PUBLIC_URL=https://YOUR_CLOUD_RUN_HOST/mcp,MCP_AUTH_ISSUER_URL=https://YOUR_OAUTH_ISSUER/,MCP_AUTH_AUDIENCE=https://YOUR_CLOUD_RUN_HOST/mcp,MCP_AUTH_JWKS_URL=https://YOUR_OAUTH_ISSUER/.well-known/jwks.json,MCP_AUTH_ALGORITHMS=RS256,MCP_REQUIRED_SCOPES=research:mcp \
  --set-secrets GITHUB_TOKEN=research-mcp-github-token:latest
```

Only after OAuth is configured and the service update succeeds, make Cloud Run reachable to remote MCP clients:

```bash
gcloud run services add-iam-policy-binding research-mcp \
  --member='allUsers' \
  --role='roles/run.invoker'
```

This makes the network endpoint reachable; the MCP application layer must still reject missing or invalid bearer tokens.

## 7. Validate before connecting a reasoning client

Health check:

```bash
curl -i https://YOUR_CLOUD_RUN_HOST/healthz
```

Unauthenticated MCP access should not yield a usable MCP session:

```bash
curl -i https://YOUR_CLOUD_RUN_HOST/mcp
```

Then validate with a real OAuth access token and an MCP-capable client using read-only tools first:

- `get_research_status()`
- `get_latest_run("COMPLETED")` when applicable
- `load_planning_context()`

For write-path testing, temporarily point `RESEARCH_GITHUB_BRANCH` at a dedicated integration-test branch instead of `main`.

## Operational defaults

- Start with `min-instances=0` and `max-instances=1`.
- Use request-based billing and budget alerts.
- Rotate the GitHub credential periodically.
- Keep the credential repository-scoped and never expose it to ChatGPT, Claude, logs, or MCP responses.
- Keep the runtime service account dedicated to this service.
- `/healthz` deliberately does not access GitHub.
- MCP HTTP mode is stateless; GitHub remains the durable source of truth.

See `.env.remote.example` for the environment-variable reference.
