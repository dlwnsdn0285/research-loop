# Research Loop

**A Git-backed research protocol with an optional MCP state layer for traceable LLM-assisted research.**

Research Loop is a lightweight human-in-the-loop workflow for research that involves LLM chats, coding agents, and repeated experiments. It keeps the durable scientific record in Git instead of allowing the current chat session—or the latest agent interpretation—to become the source of truth.

The core idea is simple:

> **Evidence, interpretation, research state, and human decisions should remain distinguishable.**

```text
Human researcher
      │
      ├───────────────┐
      ▼               ▼
 ChatGPT           Claude
 reasoning         critique
      └──────┬────────┘
             ▼
        Research MCP
      protocol / state
             ▼
           GitHub
      durable source of truth
             ▲
             │ git pull / push
        Coding Agent
      execution layer
```

Research MCP is optional for local-only workflows, but v0.2 includes a self-hostable MCP server so ChatGPT, Claude, or another MCP-capable reasoning client can share the same protocol-aware GitHub state.

## Why this exists

LLMs are useful throughout research: they propose hypotheses, design experiments, write code, inspect results, explain failures, and suggest next steps. Over long projects, however, those roles can collapse into one another. A generated report can quietly mix measurements, selected examples, interpretation, causal explanation, and new hypotheses. The next model then reads those inferences as if they were observations.

Research Loop introduces explicit boundaries:

```text
01_PLAN.md
    ↓ human approval
experiment
    ↓
raw/* + 02_RESULTS_RAW.md
    ↓
03_ANALYSIS.md
    ↓ independent review
04_CRITIQUE.md
    ↓
COMPLETED
```

Git history preserves what was known, observed, inferred, and challenged at each point.

## Fast Loop and Slow Loop

Research Loop is not a fully autonomous research agent.

**Fast Loop — machine-side execution**

- sync the latest canonical GitHub state;
- implement an approved plan;
- run experiments, retries, seeds, sanity checks, and fixed ablations;
- preserve raw outputs and execution provenance;
- validate successful runs;
- commit and push them to `RESULTS_READY`.

**Slow Loop — epistemic decisions**

- interpret results;
- compare competing explanations;
- refine hypotheses;
- choose the next experiment;
- decide go / no-go;
- determine how strongly a scientific claim is justified.

The intended escalation rule is simple: automate repetitive execution, but return consequential scientific decisions to the researcher and reasoning clients.

## Research state

Each run lives under a dated history directory:

```text
research_runs_history/
└── YYYY-MM-DD/
    └── expNN_slug/
        ├── 00_MANIFEST.yaml
        ├── 01_PLAN.md
        ├── 02_RESULTS_RAW.md
        ├── 03_ANALYSIS.md
        ├── 04_CRITIQUE.md
        └── raw/
```

Typical states are:

```text
PLANNING
  → PLAN_READY
  → PLAN_APPROVED
  → RUNNING
  → RESULTS_READY
  → ANALYZED
  → CRITIQUED
  → COMPLETED
```

`RESULTS_READY` means observations exist but official interpretation does not. `ANALYZED` means a primary analysis exists but has not yet received independent critique. `COMPLETED` is a durable parent that can safely seed the next planning cycle.

See [`RESEARCH_PROTOCOL.md`](RESEARCH_PROTOCOL.md) for the full contract.

## Quick start: local protocol

Clone and install:

```bash
git clone https://github.com/dlwnsdn0285/research-loop.git
cd research-loop
python -m pip install -e .
```

Initialize Research Loop inside an existing research repository:

```bash
research-loop init /path/to/your-project
```

This installs the protocol, manifest/plan templates, agent instructions, provider skills, and CI validation while preserving existing files.

Create a local run manually if desired:

```bash
cd /path/to/your-project
research-loop new "baseline sanity check"
research-loop validate --all
```

The generated `AGENTS.md` and `CLAUDE.md` define executor boundaries, including Git sync before execution and automatic commit/push on a successful approved path.

## Quick start: Research MCP

Install the MCP extra:

```bash
python -m pip install -e '.[mcp]'
```

Point the MCP server at **your own initialized research repository**:

```bash
export RESEARCH_GITHUB_REPO=YOUR_GITHUB_USER/YOUR_RESEARCH_REPO
export GITHUB_TOKEN=YOUR_FINE_GRAINED_GITHUB_TOKEN
export RESEARCH_GITHUB_BRANCH=main
research-mcp
```

For local Streamable HTTP testing:

```bash
research-mcp --transport streamable-http --host 127.0.0.1 --port 8000
```

The endpoint is `/mcp` and liveness is `/healthz`.

The ten semantic tools are:

| Phase | Tool | Purpose |
|---|---|---|
| State | `get_research_status` | Read deterministic loop state |
| State | `get_latest_run` | Find latest run with an exact status |
| Planning | `load_planning_context` | Load durable prior context + protocol |
| Planning | `create_planned_run` | Persist a chat-authored plan as `PLAN_READY` |
| Analysis | `load_analysis_context` | Load plan, raw summary, artifact inventory |
| Analysis | `read_run_file` | Inspect specific raw/text evidence on demand |
| Analysis | `save_analysis` | Save `03_ANALYSIS.md`, transition to `ANALYZED` |
| Critique | `load_critique_context` | Load independent-review context |
| Critique | `save_critique` | Save `04_CRITIQUE.md`, transition to `CRITIQUED` |
| Completion | `complete_run` | Validate invariants and transition to `COMPLETED` |

The MCP does not choose hypotheses or generate scientific conclusions by itself. The reasoning client combines **current chat context + durable GitHub state**, while MCP only performs allowed persistence/state operations.

A fresh project is supported: the first plan can be created without a previous `COMPLETED` run.

## Self-hosting the MCP

For remote ChatGPT/Claude access, the recommended deployment model is **one researcher/project controlling its own MCP deployment and GitHub credential**:

```text
ChatGPT / Claude
      ↓ HTTPS + OAuth/OIDC
Self-hosted Research MCP
      ↓ repo-scoped GitHub credential
Your research repository
      ↑ git push / pull
Coding Agent
```

Use [`Dockerfile.research-mcp`](Dockerfile.research-mcp) and [`research_mcp/.env.remote.example`](research_mcp/.env.remote.example) as the starting point. Keep OAuth off only for local/stdio testing. Do not expose unauthenticated HTTP mode to the public internet.

A narrowly scoped GitHub credential should have only the repository access required by your research project. Do not commit credentials, Cloud provider secrets, or private project identifiers.

See [`research_mcp/README.md`](research_mcp/README.md) for details.

## Coding Agent contract

The Coding Agent is an executor, not the scientific decision authority. On a normal run it should:

```text
sync canonical GitHub state
        ↓
read PLAN_READY / PLAN_APPROVED run
        ↓
explain execution + obtain approval
        ↓
RUNNING
        ↓
execute + validate
        ↓
preserve raw artifacts
        ↓
02_RESULTS_RAW.md + manifest provenance
        ↓
RESULTS_READY
        ↓
commit + push
```

It should stop and escalate on validation failure, merge conflict, destructive overwrite, or any material change to the approved experimental plan.

## Analysis and critique

Primary interpretation and adversarial review are deliberately separate artifacts. A useful default is:

```text
ChatGPT → 03_ANALYSIS.md
Claude  → 04_CRITIQUE.md
```

The exact providers are not important; independence is. Research MCP rejects identical analysis and critique author identities on the normal completion path.

## Optional pairing: Research Ponytail

Research Loop manages **research state and provenance**. [Research Ponytail](https://github.com/dlwnsdn0285/research-ponytail) manages **research complexity**.

They are complementary rather than coupled. Research Ponytail is useful during planning, analysis, critique, and next-step selection to focus on the smallest decisive uncertainty; it should not alter raw-result recording.

A useful mental model is:

```text
Research Ponytail decides what is worth testing.
Research Loop remembers what was actually tested.
```

## Inspiration: LLM Wiki

Research Loop was inspired in part by Andrej Karpathy's **LLM Wiki** idea file:

https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f

The relevant inspiration is the broader pattern of moving durable state out of transient conversations and into filesystem artifacts that agents can maintain over time. Research Loop applies that pattern to computational experiment lifecycles with explicit plans, human approval, raw-result isolation, analysis, critique, states, and provenance.

No text or code from the LLM Wiki gist is included in this repository. See [`NOTICE.md`](NOTICE.md) for attribution and licensing notes.

## Design principles

1. **GitHub/Git is the durable state.** Chats and agents are clients of the record, not the record itself.
2. **Observed and inferred information are different artifacts.**
3. **Plans precede the results they are intended to interpret.**
4. **Raw outputs remain minimally transformed and reproducible.**
5. **Human approval is a first-class gate for consequential execution.**
6. **Reasoning clients share one protocol rather than ad hoc filesystem mutation.**
7. **Independent critique should challenge primary analysis.**
8. **Automation removes bookkeeping, not scientific accountability.**
9. **Use the smallest experiment that materially reduces the current uncertainty.**

## Status

**v0.2 prototype.** The local Git-backed protocol and self-hostable Research MCP are implemented. Interfaces may still change as full real-world research cycles reveal friction. A stable `v1.0` should follow only after repeated end-to-end use.

## License

Research Loop is released under the MIT License. See [`LICENSE`](LICENSE).

Third-party inspiration and attribution are described in [`NOTICE.md`](NOTICE.md).
