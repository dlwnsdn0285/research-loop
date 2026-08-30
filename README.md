# Research Loop

**A Git-backed protocol for traceable LLM-assisted research.**

Research Loop is a lightweight workflow for research that involves LLMs, coding agents, and multiple chat sessions. It keeps the durable scientific record in Git instead of allowing the current chat session—or the latest agent interpretation—to become the de facto source of truth.

The core idea is simple:

> **Evidence, interpretation, and research state should not be the same thing.**

```text
01_PLAN.md
    ↓
human approval
    ↓
experiment
    ↓
raw/* + 02_RESULTS_RAW.md
    ↓
03_ANALYSIS.md
    ↓
04_CRITIQUE.md
    ↓
next plan
```

Plans are recorded before execution. Raw measurements are kept separate from interpretation. Analysis is written only after the result exists. Critique is stored separately from the analysis it evaluates. The repository retains the history even when the researcher opens a fresh ChatGPT, Claude, Codex, or Claude Code session.

## Why this exists

LLMs are useful across the full research loop: they propose hypotheses, design experiments, write code, inspect results, explain failures, and suggest what to try next. The problem is that these roles can collapse into one another.

A typical agent-generated report can quietly mix:

- measurements produced by the experiment;
- examples selected after seeing the result;
- the model's interpretation of those measurements;
- causal explanations that were not directly tested;
- and suggestions for the next experiment.

The next agent then reads that report as context, and an inference from one iteration can become an apparent fact in the next. Over a long project, it becomes increasingly difficult to reconstruct what was actually observed and what was inferred later.

Research Loop deliberately introduces boundaries.

### Raw results are not analysis

The experiment executor may write files under `raw/` and generate `02_RESULTS_RAW.md`, but those artifacts are observational. They should not contain claims such as “this suggests” or “this supports our hypothesis.”

Interpretation belongs in `03_ANALYSIS.md`.

This makes it possible for another model—or the same researcher months later—to reinterpret the same result without inheriting the first model's explanation as if it were a measurement.

### Chat is disposable; research state is not

Chat histories are useful context, but they are not a reliable scientific ledger. Research Loop treats the Git repository as the durable state:

```text
ChatGPT session ─┐
Claude session  ─┼──→ Git-backed research state
Coding agent    ─┘
```

A model can be changed, a conversation can be restarted, and different agents can perform different roles while working from the same experiment record.

### Plans come before results

Expected outcomes and their interpretations should be written before the experiment runs whenever practical. The goal is not rigid preregistration for every exploratory task; it is to make hindsight visible.

The preferred pattern is:

```text
observation → previously defined outcome branch → supported claim → remaining uncertainty
```

rather than:

```text
observation → post-hoc story → another experiment → another post-hoc story
```

### Human approval remains a gate

Automation should remove repetitive bookkeeping, not remove the researcher from consequential decisions. By default, an executor first summarizes the plan and waits for explicit approval before changing the run state to `RUNNING`.

## Experiment state

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

See [`RESEARCH_PROTOCOL.md`](RESEARCH_PROTOCOL.md) for the full contract.

## Quick start

Clone this repository and install the small CLI:

```bash
git clone https://github.com/dlwnsdn0285/research-loop.git
cd research-loop
pip install -e .
```

Initialize Research Loop inside an existing research repository:

```bash
research-loop init /path/to/your-project
```

Create a run:

```bash
cd /path/to/your-project
research-loop new "baseline sanity check"
```

Validate the research history:

```bash
research-loop validate --all
```

The generated `AGENTS.md` and `CLAUDE.md` explain the role boundaries to coding agents. Provider-specific skills under [`skills/`](skills/) reduce repetitive prompts for planning, execution, and analysis.

## Roles

Research Loop intentionally separates four roles:

| Role | Main responsibility | May interpret results? |
|---|---|---:|
| Planner | Turn prior evidence and the current question into a testable plan | Yes, before execution |
| Executor | Implement and run the approved plan; preserve raw artifacts | **No** |
| Analyst | Map observed results back to the plan and state supported/unsupported claims | Yes |
| Critic | Challenge the analysis, confounders, validity, and overclaiming | Yes |

The same model can perform multiple roles at different times, but the artifacts remain separate.

## Optional pairing: Research Ponytail

Research Loop manages **research state and provenance**. [Research Ponytail](https://github.com/dlwnsdn0285/research-ponytail) manages **research complexity**.

They are complementary rather than coupled.

Research Ponytail is most useful in the reasoning-heavy parts of the loop:

- **Planning:** identify the root uncertainty and choose the smallest decisive experiment instead of automatically expanding the experiment matrix.
- **Analysis:** state the minimum conclusion justified by the evidence and avoid turning every result into a large mechanism story.
- **Critique / next-step selection:** focus on the most credible failure mode and the one follow-up that could materially change the conclusion.

It should **not** alter the raw-result layer. The executor should record what happened regardless of which reasoning policy is used later.

A useful mental model is:

```text
Research Ponytail decides what is worth testing.
Research Loop remembers what was actually tested.
```

Research Ponytail is optional; Research Loop does not depend on it. See [`integrations/research-ponytail/README.md`](integrations/research-ponytail/README.md).

## Inspiration: LLM Wiki

Research Loop was inspired in part by Andrej Karpathy's **LLM Wiki** idea file:

https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f

The relevant inspiration is the broader pattern of moving durable state out of transient conversations and into filesystem artifacts that agents can maintain over time, while keeping original/source material distinguishable from LLM-maintained derived material and using repository-level instructions to govern agent behavior.

Research Loop applies that general pattern to a different problem: the lifecycle of computational experiments. It adds explicit pre-execution plans, approval gates, raw-result isolation, post-result analysis, adversarial critique, run states, and provenance tracking.

No text or code from the LLM Wiki gist is included in this repository. See [`NOTICE.md`](NOTICE.md) for attribution and licensing notes.

## Design principles

1. **Git is the durable state.** Chats and agents are clients of the record, not the record itself.
2. **Observed and inferred information are different artifacts.**
3. **Raw outputs should be reproducible and minimally transformed.**
4. **Plans should precede the results they are meant to interpret.**
5. **Human approval is a first-class state transition.**
6. **Provider independence matters.** ChatGPT, Claude, Codex, or another agent may take over at any stage.
7. **Automation should reduce bookkeeping without hiding provenance.**

## What v0.1 does not try to solve

Research Loop v0.1 is intentionally small. It does not provide a hosted database, experiment scheduler, or universal research agent. It also does not require an MCP server.

The local Git-backed protocol is the foundation. A future Research MCP layer can make operations such as “find the latest `RESULTS_READY` run” and “save this approved plan” provider-neutral without changing the underlying record format.

## Status

Prototype / v0.1. The format is usable, but interfaces may still change as it is tested across research projects and agent providers.

## License

Research Loop is released under the MIT License. See [`LICENSE`](LICENSE).

Third-party inspiration and attribution are described in [`NOTICE.md`](NOTICE.md).
