# Research Loop

[한국어 README](README_KO.md)

**A human-in-the-loop research protocol for LLM- and Coding-Agent-assisted research: automate execution quickly, while keeping scientific interpretation understandable and interruptible by the human researcher.**

> **Automate execution, keep raw results separate from interpretation, and return consequential research decisions to a Human + Chat Slow Loop.**

---

# 1. Core Philosophy

LLMs and Coding Agents can dramatically accelerate experiment implementation and execution. As experiments become faster, however, a new bottleneck appears: the researcher must still understand what changed, catch errors, and decide which question should come next.

Research Loop addresses that bottleneck with the following principles.

## 1.1 Separate the Fast Loop and the Slow Loop

Explicit and repetitive tasks are handled by the Coding Agent.

```text
Fast Loop

implementation
→ execution
→ retries / seeds / sanity checks
→ validation
→ raw-result recording
```

Interpretation and scientific decisions are escalated to the Slow Loop.

```text
Slow Loop

understand the result
→ ask questions
→ challenge / debate
→ refine hypotheses
→ choose the next experiment
```

In short:

> **Automate execution; escalate uncertain scientific judgment.**

## 1.2 Separate Coding Agents from Chat

A Coding Agent and ChatGPT/Claude may use similar underlying model families, but they operate inside different **harnesses**.

```text
Coding Agent
→ optimized for editing / execution / debugging

Chat
→ optimized for explanation / questioning / discussion / decisions
```

Research Loop therefore treats them as different interfaces:

- **Coding Agent = execution**
- **Chat = reasoning with the human**

The Coding Agent preserves what happened as **Raw Result** rather than immediately turning it into an official scientific story. Interpretation happens later in the Human + Chat Slow Loop.

## 1.3 Separate Raw Result from Inference

LLM interpretation is useful, but it can be wrong. If one model's interpretation is repeatedly summarized and passed into the next model, small errors can gradually accumulate and begin to look like facts.

```text
Experiment Output
       ↓
   RAW RESULT
       ↓
  Human + Chat
       ↓
    ANALYSIS
       ↓
Independent CRITIQUE
```

Research Loop therefore keeps **observations and interpretations as different artifacts**.

- `raw/*`, `02_RESULTS_RAW.md` = observation
- `03_ANALYSIS.md` = primary inference
- `04_CRITIQUE.md` = independent/adversarial inference

## 1.4 Human-in-the-loop is not just an approval button

A common Human-in-the-loop pattern looks like this:

```text
Agent proposal
      ↓
    Human
Approve / Reject
```

That works best when the human already understands the problem well enough to judge immediately.

Research Loop instead uses Chat as the Slow Loop interface:

```text
Raw Result
   ↓
Chat explains
   ↓
Human asks questions
   ↓
debate / challenge
   ↓
shared understanding
   ↓
Human Decision
```

The human therefore participates in **forming the interpretation itself**, not merely approving a finished proposal.

When an analysis or plan is finally persisted, the reasoning client combines:

```text
CURRENT CHAT CONTEXT
        +
DURABLE GITHUB STATE
        ↓
research inference
```

## 1.5 Preserve Provenance

Research Loop does not preserve only the latest conclusion. Each run retains its parent experiment, plan, raw result, analysis, critique, author/provider information, and state transitions.

```text
Experiment 1
    ↓
Experiment 2
    ↓
Experiment 3
```

If a later result overturns an earlier interpretation, the old analysis is not rewritten as if it never existed. The next run records **why the judgment changed**.

The repository therefore becomes a record of **how uncertainty was reduced**, not merely a folder containing the latest story.

## 1.6 Research State is controlled by MCP, not by the LLM

The LLM reasons about the research, but it does not freely mutate the research protocol.

```text
LLM
 │
 │ "save analysis"
 ▼
Research MCP
 │
 ├─ Is the run RESULTS_READY?
 ├─ Does an analysis already exist?
 ├─ Is provenance valid?
 └─ Is the transition allowed?
 │
 ▼
GitHub
```

In short:

> **The LLM reasons; MCP enforces the protocol.**

The state machine is:

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

## 1.7 ChatGPT and Claude role split

Research Loop itself is provider-independent. The repository's default workflow uses the following **operational heuristic**, based on practical experience rather than a universal claim about model quality:

```text
ChatGPT
  └─ relatively broad / lightweight exploration
     └─ easy-to-follow explanation
        └─ useful for initial planning / primary analysis

Claude
  └─ relatively narrow / deep inspection
     └─ aggressive examination of assumptions
        └─ useful for independent critique
```

A useful default is therefore:

```text
Human + ChatGPT → plan / primary analysis
Claude          → independent critique
```

The provider names are not the important part. The important requirement is that **primary analysis and critique are meaningfully independent**.

---

# 2. Actual Architecture

```text
                    Human
                      │
           questions / understanding / decisions
                      │
          ┌───────────┴───────────┐
          ▼                       ▼
      ChatGPT                   Claude
  Planning / Analysis           Critique
          │                       │
          └───────────┬───────────┘
                      ▼
                 Research MCP
             Protocol / State Layer
                      │
                      ▼
                    GitHub
              Source of Truth
                      ▲
                      │ pull / push
                      │
                Coding Agent
             Experiment Execution
```

| Component | Responsibility |
|---|---|
| **Human** | Final scientific decision authority |
| **ChatGPT** | Initial planning, explanation, primary analysis |
| **Claude** | Independent critique |
| **Coding Agent** | Code implementation, experiment execution, validation |
| **Research MCP** | Semantic operations, state transitions, protocol validation |
| **GitHub** | Durable research state / provenance / Source of Truth |

## 2.1 Run structure

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

```text
Run
├─ Manifest        → identity / state / provenance / artifact registry
├─ Plan            → pre-result hypotheses and decision branches
├─ Raw Results     → observations only
├─ Analysis        → primary interpretation
└─ Critique        → independent adversarial review
```

See [`RESEARCH_PROTOCOL.md`](RESEARCH_PROTOCOL.md) for the complete protocol contract.

## 2.2 The ten Research MCP semantic tools

| Phase | Tool | Purpose |
|---|---|---|
| State | `get_research_status` | Read deterministic loop state |
| State | `get_latest_run` | Find the latest run with an exact status |
| Planning | `load_planning_context` | Load durable prior context + protocol |
| Planning | `create_planned_run` | Persist a chat-authored plan as `PLAN_READY` |
| Analysis | `load_analysis_context` | Load plan, raw summary, and artifact inventory |
| Analysis | `read_run_file` | Inspect specific raw/text evidence on demand |
| Analysis | `save_analysis` | Save `03_ANALYSIS.md` and transition to `ANALYZED` |
| Critique | `load_critique_context` | Load context for independent critique |
| Critique | `save_critique` | Save `04_CRITIQUE.md` and transition to `CRITIQUED` |
| Completion | `complete_run` | Validate invariants and transition to `COMPLETED` |

Research MCP does not independently choose hypotheses or generate scientific conclusions.

---

# 3. Actual Workflow

One research cycle looks like this:

```text
             ┌──────────────────────┐
             │      SLOW LOOP       │
             │                      │
             │ Human + ChatGPT      │
             │ understand / question│
             │ design next experiment│
             └──────────┬───────────┘
                        │
                   PLAN_READY
                        │
                        ▼
             ┌──────────────────────┐
             │      FAST LOOP       │
             │                      │
             │ Coding Agent         │
             │ implement → execute  │
             │ → validate           │
             │ → raw result         │
             └──────────┬───────────┘
                        │
                  RESULTS_READY
                        │
                        ▼
             ┌──────────────────────┐
             │      SLOW LOOP       │
             │                      │
             │ ChatGPT Analysis     │
             │        ↓             │
             │ Claude Critique      │
             │        ↓             │
             │ Human Decision       │
             └──────────┬───────────┘
                        │
                    COMPLETED
                        │
                        ▼
                 Next Experiment
```

In artifact terms:

```text
01_PLAN.md
     ↓
Human approval
     ↓
Coding Agent
     ↓
raw/* + 02_RESULTS_RAW.md
     ↓
ChatGPT + Human
     ↓
03_ANALYSIS.md
     ↓
Claude
     ↓
04_CRITIQUE.md
     ↓
Human Decision
     ↓
COMPLETED
     ↓
parent of the next run
```

## In one sentence

> **Research Loop gives repetitive experiment execution to Coding Agents, preserves Raw Results separately from interpretation, and uses a Human + Chat Slow Loop to understand, debate, and decide what the evidence means before the next research step is committed.**

---

# 4. Installation and Usage

## 4.1 Local protocol only

```bash
git clone https://github.com/dlwnsdn0285/research-loop.git
cd research-loop
python -m pip install -e .
```

Initialize Research Loop inside an existing research repository:

```bash
research-loop init /path/to/your-project
```

Create a local run manually if desired:

```bash
cd /path/to/your-project
research-loop new "baseline sanity check"
research-loop validate --all
```

This local mode does not require MCP.

## 4.2 Add Research MCP

```bash
python -m pip install -e '.[mcp]'
```

Point the MCP server at your own research repository:

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

The MCP endpoint is `/mcp`; liveness is `/healthz`.

## 4.3 Remote / self-hosted MCP

The recommended deployment model is **one researcher/project controlling its own MCP deployment and GitHub credential**.

```text
ChatGPT / Claude
      ↓ HTTPS + OAuth/OIDC
Self-hosted Research MCP
      ↓ repo-scoped GitHub credential
Your research repository
      ↑ git push / pull
Coding Agent
```

Deployment files:

- [`Dockerfile.research-mcp`](Dockerfile.research-mcp)
- [`cloudbuild.research-mcp.yaml`](cloudbuild.research-mcp.yaml)
- [`research_mcp/.env.remote.example`](research_mcp/.env.remote.example)

See [`research_mcp/CLOUD_RUN.md`](research_mcp/CLOUD_RUN.md) for a generic Google Cloud Run walkthrough.

---

# 5. Usage Example

The intended user experience is to speak in **research language**, not MCP API language.

### 1) Check current research state

> What is the current research status?

A reasoning client may internally call `get_research_status()`, but the user does not need to remember the tool name.

### 2) Discuss the next experiment

> Let's decide the next experiment using the previous result and critique. I also want to test whether the effect survives a stricter control.

```text
load_planning_context()
        +
current conversation
        ↓
Human + ChatGPT discussion
        ↓
final experiment plan
        ↓
create_planned_run(...)
        ↓
PLAN_READY
```

### 3) Coding Agent executes

```text
sync latest GitHub state
        ↓
read plan
        ↓
explain implementation
        ↓
request approval
        ↓
execute + validate
        ↓
raw/config, raw/metrics, logs ...
        ↓
02_RESULTS_RAW.md
        ↓
RESULTS_READY
        ↓
commit + push
```

### 4) Primary analysis in Chat

> Analyze the latest result. Verify important claims against raw artifacts and explain the result so I can understand what changed.

```text
load_analysis_context()
        ↓
read_run_file(...) when needed
        ↓
conversation with human
        ↓
03_ANALYSIS.md
```

### 5) Independent critique

A useful default is:

```text
ChatGPT → primary analysis
Claude  → critique
```

The critic re-checks assumptions, confounders, comparison fairness, overclaiming, and alternative explanations.

### 6) Human judgment and completion

```text
CRITIQUED
    ↓
Human judgment
    ↓
complete_run()
    ↓
COMPLETED
```

The next planning cycle can use this run as parent provenance.

---

# 6. Additional Notes / Warnings / Roadmap

## Warning: model roles are heuristics

The ChatGPT-planner / Claude-critic split is a practical heuristic, not a universal benchmark claim. Use whichever providers or models produce sufficiently independent reasoning in your environment.

## Warning: Research MCP is not a scientific agent

Research MCP should not:

- invent the next research question;
- choose between competing scientific explanations;
- silently rewrite an experiment plan;
- convert raw measurements into causal claims;
- decide that a surprising result should launch a new research direction.

Those decisions belong in the Slow Loop.

## Warning: Raw Results must remain raw

An executor should not rewrite `02_RESULTS_RAW.md` to make a preferred interpretation more persuasive. Raw artifacts should remain minimally transformed and reproducible.

## Warning: remote MCP requires real security boundaries

Do not expose auth-off HTTP mode to the public internet.

Recommended properties include:

- HTTPS;
- OAuth/OIDC;
- repository-scoped GitHub credentials;
- Secret Manager injection rather than committed tokens;
- one researcher/project per MCP deployment unless proper multi-tenant isolation is intentionally implemented.

## Optional: Research Ponytail

Research Loop manages **research state and provenance**. [Research Ponytail](https://github.com/dlwnsdn0285/research-ponytail) manages **research complexity**.

```text
Research Ponytail decides what is worth testing.
Research Loop remembers what was actually tested.
```

Research Ponytail is most useful for planning, analysis, critique, and next-step selection. It should not alter the raw-result layer.

## Inspiration: LLM Wiki

Research Loop was inspired in part by Andrej Karpathy's **LLM Wiki** idea file:

https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f

The relevant inspiration is the broader idea of moving durable state out of transient conversations and into filesystem artifacts, while keeping source material distinguishable from LLM-derived material.

Research Loop applies that pattern to computational experiment lifecycles with explicit plans, human approval, raw-result isolation, analysis, critique, state, and provenance.

No text or code from the LLM Wiki gist is included in this repository. See [`NOTICE.md`](NOTICE.md) for attribution and licensing notes.

## Current limitation: Coding Agent repository synchronization

In v0.2, the normal executor path assumes that the Coding Agent works from a local checkout and synchronizes the canonical GitHub repository before execution.

```text
GitHub canonical repo
        ↓ git pull / fetch
local research checkout
        ↓
Coding Agent execution
```

This creates friction around stale local checkouts, merge conflicts, and repository mismatch.

## Roadmap: direct GitHub source access for Coding Agents

A future version should reduce the assumption that every run begins with a correctly synchronized local checkout.

```text
Current v0.2
GitHub → pull → Local checkout → Coding Agent

Future direction
GitHub canonical source → Coding Agent execution workspace → results → GitHub
```

This still requires a clear protocol for writable working trees, uncommitted changes, authentication, and reproducibility.

## Open question: Claude Code and repository identity

For example:

```text
Claude Code current workspace
        = local/project-A

Research MCP durable repo
        = github.com/user/project-B
```

Open questions include:

- Which repository is authoritative for source code?
- Should execution be refused when local `origin` differs from the durable repository?
- Can the research-state repository and experiment-code repository intentionally differ?
- If so, how should commit SHAs and provenance connect the two repositories?
- Should MCP expose canonical repository identity to the Coding Agent before execution?

Until this is formalized, repository mismatch or unexpected divergence should be treated as an **escalation condition rather than something the agent guesses through**.

## Status

**v0.2 prototype.** The local Git-backed protocol and self-hostable Research MCP are implemented. Interfaces may change as repeated real-world end-to-end research cycles reveal friction.

A stable `v1.0` should follow only after multiple complete planning → execution → analysis → critique cycles.

## License

Research Loop is released under the MIT License. See [`LICENSE`](LICENSE).

Third-party inspiration and attribution are described in [`NOTICE.md`](NOTICE.md).
