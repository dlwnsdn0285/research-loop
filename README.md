# Research Loop

**A Git-backed research protocol with an optional MCP state layer for traceable, human-in-the-loop LLM-assisted research.**

Research Loop is a lightweight workflow for research that involves LLM chats, coding agents, and repeated experiments. It keeps the durable scientific record in Git instead of allowing the current chat session—or the latest agent interpretation—to become the source of truth.

The core idea is simple:

> **Evidence, interpretation, research state, and human decisions should remain distinguishable.**

---

# 1. Philosophy

## 1.1 Why this exists

LLMs are useful throughout research: they propose hypotheses, design experiments, write code, inspect results, explain failures, and suggest next steps. Over long projects, however, those roles can collapse into one another.

A generated report can quietly mix:

- measurements produced by an experiment;
- examples selected after seeing the result;
- interpretation of those measurements;
- causal explanations that were not directly tested;
- suggestions for the next experiment.

The next model then reads that report as context, and an inference from one iteration can gradually become an apparent fact in the next. At the same time, faster coding agents can keep producing experiments faster than a human researcher can fully understand what changed, why it changed, and what should be questioned next.

Research Loop is built around this bottleneck:

> **Automation can accelerate experiments faster than a human can understand and follow up on them.**

The goal is therefore not to build a fully autonomous research agent. The goal is to automate repetitive execution while preserving a slower reasoning interface in which the researcher can understand, challenge, and ultimately decide what the evidence means.

```text
                 FAST LOOP
          machine-side execution
                    │
                    │ produces
                    ▼
              RAW EVIDENCE
                    │
                    │ escalates when
                    │ interpretation matters
                    ▼
                 SLOW LOOP
        human + conversational LLM
                    │
         understand → question → debate
                    │
                    ▼
             HUMAN CONSENSUS
                    │
                    ▼
             next experiment
```

## 1.2 Fast Loop and Slow Loop

Research Loop deliberately separates two speeds of work.

### Fast Loop — machine-side execution

Typical Fast Loop work includes:

- syncing the latest canonical GitHub state;
- implementing an approved plan;
- running experiments;
- retrying failed runs;
- adding fixed seeds;
- metric aggregation;
- baseline reproduction;
- predetermined ablations;
- sanity checks;
- preserving raw outputs and execution provenance;
- validating successful runs;
- committing and pushing results to `RESULTS_READY`.

These tasks are usually explicit, repetitive, and machine-facing.

### Slow Loop — epistemic decisions

The Slow Loop handles questions such as:

- What does this result actually justify?
- Which competing explanation is still plausible?
- Is a result strong enough to change the working hypothesis?
- What is the smallest next experiment that could materially reduce uncertainty?
- Is the current method story overclaiming?
- Should the project continue, pivot, or stop?

The intended escalation rule is simple:

> **Automate execution; escalate scientific uncertainty.**

The Slow Loop is not merely an approval dialog. The conversational model helps the researcher understand the current state, explains unfamiliar details, answers follow-up questions, and challenges the interpretation until the researcher can make an informed decision.

## 1.3 Why conversational chat and coding agents are separated

A coding agent and a chat product may use related or even identical underlying model families, but they operate inside different **harnesses**.

A coding-agent harness is optimized for work:

- repository inspection;
- editing files;
- running commands;
- debugging;
- repeated execution;
- manipulating machine state.

A conversational-chat harness is optimized for interaction with a human:

- explanation;
- iterative questioning;
- reframing;
- disagreement;
- comparison of interpretations;
- maintaining a discussion until the user understands the issue well enough to decide.

Research Loop therefore treats them as different interfaces even when the underlying model is similar.

```text
                 Human researcher
                       │
               conversational interface
                       │
             understand / challenge
                       │
                       ▼
                 ChatGPT / Claude
                 reasoning interface
                       │
                       │ semantic operation
                       ▼
                  Research MCP
                       │
                       ▼
                     GitHub
               durable source of truth
                       ▲
                       │ git pull / push
                       │
                  Coding Agent
                execution interface
```

The coding agent is intentionally kept away from official scientific interpretation while acting as executor. Its job is to report what happened, not to turn the result into a story.

## 1.4 Raw result and inference are different artifacts

Research Loop separates observation from interpretation.

```text
01_PLAN.md
    ↓ human approval
experiment
    ↓
raw/* + 02_RESULTS_RAW.md   ← observation
    ↓
03_ANALYSIS.md              ← inference
    ↓ independent review
04_CRITIQUE.md              ← adversarial inference
    ↓
COMPLETED
```

The executor may write files under `raw/` and generate `02_RESULTS_RAW.md`, but those artifacts should remain observational. They should not silently contain claims such as “this proves,” “this suggests the mechanism is,” or “the next experiment should be.”

Interpretation belongs in `03_ANALYSIS.md` and `04_CRITIQUE.md`.

This distinction matters because human-readable inference is useful but fallible. If inference is repeatedly summarized, compressed, and passed from one agent to another, errors can accumulate. By preserving the original measurements separately, another model—or the same researcher months later—can reinterpret the same evidence without inheriting the previous explanation as if it were a measurement.

## 1.5 Human-in-the-loop as a conversation, not a binary gate

Many human-in-the-loop systems place the human at a narrow decision point:

```text
agent proposes action
       ↓
 human: approve / reject
```

This can work well when the human already has enough expertise and context to judge the proposal immediately. In long-running research, however, the bottleneck is often that the human first needs to **understand why the decision matters**.

Research Loop uses conversational chat as the Slow Loop interface:

```text
raw evidence
    ↓
chat explains current state
    ↓
human asks basic or expert questions
    ↓
chat answers / challenges / compares alternatives
    ↓
shared working understanding
    ↓
human decision
```

The researcher can therefore intervene before the inference becomes durable research state. The conversation may include corrections, doubts, new constraints, and questions that were not present in GitHub yet. When an analysis or next plan is finally persisted, the reasoning client combines:

```text
CURRENT CHAT CONTEXT
        +
DURABLE GITHUB STATE
        ↓
research inference
```

This makes the human role richer than a simple approval button: the human can participate in forming the interpretation itself.

## 1.6 Provenance: preserve how the conclusion changed

Research Loop does not keep only the latest conclusion.

Each run preserves:

- its parent experiment;
- its pre-execution plan;
- the raw result;
- the primary analysis;
- the independent critique;
- author/provider provenance;
- state transitions.

A later experiment may overturn an earlier interpretation. In that case, the earlier analysis is not deleted and rewritten as if it never existed. Instead, the next run records why the interpretation changed.

The repository therefore becomes a history of **how uncertainty was reduced**, not merely a folder containing the latest story.

## 1.7 Why MCP controls the state machine

The LLM should reason about research; it should not freely mutate the research protocol.

Research Loop therefore exposes semantic operations through Research MCP rather than allowing every reasoning client to edit protocol files arbitrarily.

```text
Reasoning client
      │
      │ "save analysis"
      ▼
Research MCP
      │
      ├─ Is the run RESULTS_READY?
      ├─ Is analysis already present?
      ├─ Is provenance valid?
      └─ Is the next transition allowed?
      │
      ▼
GitHub
```

This is similar to using a transaction/API instead of allowing every client to mutate database files directly.

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

`RESULTS_READY` means observations exist but official interpretation does not. `ANALYZED` means a primary analysis exists but has not yet received independent critique. `COMPLETED` is a durable parent that can safely seed the next planning cycle.

## 1.8 Why ChatGPT for planning and Claude for critique?

Research Loop is provider-independent. ChatGPT, Claude, or another capable model can take any reasoning role.

That said, the workflow that motivated this repository uses the following **operational heuristic**, based on the author's practical experience rather than a universal claim about the models:

```text
ChatGPT
  └─ broader / lighter exploration
     └─ easy-to-follow explanation
        └─ useful for initial planning with the human

Claude
  └─ narrower / deeper inspection
     └─ aggressive examination of assumptions
        └─ useful for independent critique
```

A useful default is therefore:

```text
Human + ChatGPT → plan / primary interpretation
Claude          → independent critique
```

The exact providers are not important. What matters is that the primary interpretation and adversarial review are meaningfully independent.

Research MCP enforces one minimal version of this principle by rejecting identical analysis and critique author identities on the normal completion path.

## 1.9 Design principles

1. **GitHub/Git is the durable state.** Chats and agents are clients of the record, not the record itself.
2. **Observed and inferred information are different artifacts.**
3. **Plans precede the results they are intended to interpret.**
4. **Raw outputs remain minimally transformed and reproducible.**
5. **Human approval is a first-class gate for consequential execution.**
6. **The Slow Loop should help the human understand before asking the human to decide.**
7. **Coding-agent execution and conversational inference are intentionally separated.**
8. **Reasoning clients share one protocol rather than performing ad hoc filesystem mutation.**
9. **Independent critique should challenge primary analysis.**
10. **Automation removes bookkeeping, not scientific accountability.**
11. **Preserve provenance instead of overwriting earlier interpretations.**
12. **Use the smallest experiment that materially reduces the current uncertainty.**

---

# 2. Actual Architecture

## 2.1 Components and responsibilities

```text
                Human Researcher
                       │
          ┌────────────┴────────────┐
          │                         │
     ChatGPT Chat               Claude Chat
   planning / analysis        independent critique
          │                         │
          └──────────┬──────────────┘
                     ▼
                Research MCP
             protocol / state layer
                     │
                     ▼
                   GitHub
          durable research source of truth
                     ▲
                     │ git pull / push
                     │
                Coding Agent
              execution on lab/GPU
```

### Human Researcher — decision authority

The human decides:

- which scientific claim to trust;
- whether an explanation is plausible;
- whether another experiment is needed;
- which experiment is worth running next;
- how strongly a conclusion can be stated.

### ChatGPT / Claude — interactive reasoning layer

The chat models:

- form and compare hypotheses;
- explain evidence;
- design experiments;
- interpret results;
- challenge assumptions;
- discuss uncertainty with the researcher.

They combine the current conversation with durable state loaded through Research MCP.

### Research MCP — protocol / persistence layer

Research MCP does **not** perform scientific reasoning. It:

- reads durable research state;
- exposes allowed semantic operations;
- persists already-authored plans, analyses, and critiques;
- validates state transitions;
- enforces provenance and completion invariants.

### GitHub — durable state / provenance layer

GitHub stores the versioned research record:

- plan;
- manifest/state;
- raw results;
- analysis;
- critique;
- provenance;
- experiment lineage.

### Coding Agent — execution layer

The Coding Agent:

- synchronizes the latest repository state;
- reads the approved plan;
- implements and runs experiments;
- performs validation and sanity checks;
- records raw results and logs;
- updates execution provenance;
- commits and pushes successful runs to `RESULTS_READY`.

It should not independently select the next scientific hypothesis while acting as executor.

## 2.2 Run structure

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

Conceptually:

```text
Run
├─ Manifest        → identity / state / provenance / artifact registry
├─ Plan            → pre-result hypotheses and decision branches
├─ Raw Results     → observations only
├─ Analysis        → primary interpretation
└─ Critique        → independent adversarial review
```

See [`RESEARCH_PROTOCOL.md`](RESEARCH_PROTOCOL.md) for the full contract.

## 2.3 The ten Research MCP tools

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

The MCP does not choose hypotheses or generate scientific conclusions by itself.

A fresh project is supported: the first plan can be created without a previous `COMPLETED` run.

## 2.4 Coding Agent contract

On a normal successful path:

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

The generated `AGENTS.md` and `CLAUDE.md` define these executor boundaries.

The Coding Agent should stop and escalate when:

- validation fails;
- a merge conflict or unexpected divergence exists;
- an existing raw artifact would be destructively overwritten;
- the approved experimental design must materially change;
- execution reveals a new scientific decision rather than a mechanical retry.

## 2.5 Analysis and critique

Primary interpretation and adversarial review are deliberately separate artifacts.

```text
RESULTS_READY
     ↓
primary analyst
     ↓
03_ANALYSIS.md
     ↓
ANALYZED
     ↓
independent critic
     ↓
04_CRITIQUE.md
     ↓
CRITIQUED
```

The same provider may technically be used in different contexts, but the normal Research MCP path requires distinct author identities for analysis and critique before completion.

---

# 3. Installation and Usage

## 3.1 Quick start: local protocol only

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

This local mode does not require MCP.

## 3.2 Add Research MCP

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

## 3.3 Remote / self-hosted MCP

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

Use:

- [`Dockerfile.research-mcp`](Dockerfile.research-mcp)
- [`cloudbuild.research-mcp.yaml`](cloudbuild.research-mcp.yaml)
- [`research_mcp/.env.remote.example`](research_mcp/.env.remote.example)

A complete generic Google Cloud Run walkthrough is in [`research_mcp/CLOUD_RUN.md`](research_mcp/CLOUD_RUN.md).

Keep OAuth off only for local/stdio testing. Do not expose unauthenticated HTTP mode to the public internet.

A narrowly scoped GitHub credential should have only the repository access required by your research project. Do not commit credentials, cloud-provider secrets, or private project identifiers.

See [`research_mcp/README.md`](research_mcp/README.md) for MCP details.

## 3.4 Normal operating cycle

Once the repository and clients are connected, the intended cycle is:

```text
[Slow Loop]
Human + ChatGPT
    ↓
load durable context
    ↓
discuss uncertainty
    ↓
write plan
    ↓
PLAN_READY

[Fast Loop]
Coding Agent
    ↓
user approval
    ↓
implementation / experiment / validation
    ↓
raw results
    ↓
RESULTS_READY

[Slow Loop]
ChatGPT
    ↓
03_ANALYSIS.md
    ↓
Claude
    ↓
04_CRITIQUE.md
    ↓
Human judgment
    ↓
COMPLETED
    ↓
next cycle
```

---

# 4. Usage Example

The point of Research Loop is that the researcher should normally talk in **research language**, not MCP API language.

## Step 1 — start from the current research state

The researcher can simply ask:

> What is the current research status?

A reasoning client may internally call:

```text
get_research_status()
```

but the researcher does not need to remember the tool name.

## Step 2 — discuss the next experiment

The researcher says:

> Let's decide the next experiment. Use the previous result and critique, but I also want to check whether the effect survives a stricter control.

The planner loads durable context:

```text
load_planning_context()
        +
current conversation
        ↓
Human + ChatGPT discussion
        ↓
final experiment plan
```

The researcher can ask basic questions, challenge assumptions, or change constraints before the plan becomes durable state.

When both sides are satisfied:

```text
create_planned_run(...)
        ↓
PLAN_READY
```

## Step 3 — Coding Agent executes the plan

The researcher asks the coding agent to run the latest experiment.

The Coding Agent:

```text
pull / sync latest GitHub state
        ↓
read plan
        ↓
explain implementation
        ↓
request approval
        ↓
execute
        ↓
validate
        ↓
record raw/config, raw/metrics, logs, etc.
        ↓
write 02_RESULTS_RAW.md
        ↓
RESULTS_READY
        ↓
commit + push
```

At this point, no official scientific interpretation has been written yet.

## Step 4 — primary analysis in chat

Back in the conversational interface, the researcher says:

> Analyze the latest result. Verify the important claims against the raw artifacts, and explain the result so I can understand what changed.

The reasoning client may use:

```text
load_analysis_context()
        ↓
read_run_file(...) when needed
        ↓
conversation with human
        ↓
03_ANALYSIS.md
```

The human can ask questions such as:

- Why is condition A stronger than B?
- Does this actually rule out the previous explanation?
- Are the evaluation sets identical?
- Could this be an artifact of the baseline?
- What is the weakest claim we can safely make?

Only after the interpretation is sufficiently understood should it be persisted with `save_analysis(...)`.

## Step 5 — independent critique

A second reasoning client then reviews the analyzed run.

A useful default is:

```text
ChatGPT → primary analysis
Claude  → critique
```

The critic sees the raw-artifact inventory as well as the primary analysis and challenges:

- hidden assumptions;
- confounders;
- fairness of comparisons;
- overclaiming;
- missing alternative explanations;
- whether the proposed next step actually discriminates between hypotheses.

The result is saved as `04_CRITIQUE.md`.

## Step 6 — human judgment and completion

The researcher compares analysis and critique, discusses any remaining disagreement, and decides whether the run can become durable parent context.

```text
CRITIQUED
    ↓
Human judgment
    ↓
complete_run()
    ↓
COMPLETED
```

The next planning cycle can now use this run as provenance rather than relying on chat memory.

---

# 5. Additional Notes, Warnings, and Roadmap

## 5.1 Warning: model-role assignments are heuristics, not guarantees

The ChatGPT-planner / Claude-critic split reflects the author's practical experience with these products and harnesses. It is **not** a benchmark claim that one model is universally broader, deeper, better at planning, or better at critique.

Use whichever providers produce sufficiently independent reasoning in your environment.

## 5.2 Warning: Research MCP is not a scientific agent

Research MCP is intentionally narrow.

It should not:

- invent the next research question;
- choose between competing scientific explanations;
- silently rewrite an experiment plan;
- convert raw measurements into causal claims;
- decide that a surprising result should launch a new research direction.

Those decisions belong in the Slow Loop.

## 5.3 Warning: raw results must remain raw

Do not let an executor make `02_RESULTS_RAW.md` more persuasive by rewriting results around a preferred interpretation.

Raw artifacts should remain minimally transformed and reproducible. Interpretation belongs later.

## 5.4 Warning: remote MCP requires real security boundaries

Do not expose auth-off HTTP mode to the public internet.

Recommended deployment properties include:

- HTTPS;
- OAuth/OIDC protection;
- repository-scoped GitHub credentials;
- secret-manager injection rather than committed tokens;
- one researcher/project per MCP deployment unless proper multi-tenant isolation is intentionally implemented.

See [`research_mcp/CLOUD_RUN.md`](research_mcp/CLOUD_RUN.md).

## 5.5 Optional pairing: Research Ponytail

Research Loop manages **research state and provenance**. [Research Ponytail](https://github.com/dlwnsdn0285/research-ponytail) manages **research complexity**.

They are complementary rather than coupled.

Research Ponytail is most useful during:

- planning — identify the root uncertainty and choose the smallest decisive experiment;
- analysis — state the minimum conclusion justified by the evidence;
- critique / next-step selection — focus on the most credible failure mode and the follow-up that could materially change the conclusion.

It should not alter the raw-result layer.

A useful mental model is:

```text
Research Ponytail decides what is worth testing.
Research Loop remembers what was actually tested.
```

## 5.6 Inspiration: LLM Wiki

Research Loop was inspired in part by Andrej Karpathy's **LLM Wiki** idea file:

https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f

The relevant inspiration is the broader pattern of moving durable state out of transient conversations and into filesystem artifacts that agents can maintain over time, while keeping source material distinguishable from LLM-maintained derived material.

Research Loop applies that pattern to computational experiment lifecycles with explicit plans, human approval, raw-result isolation, analysis, critique, states, and provenance.

No text or code from the LLM Wiki gist is included in this repository. See [`NOTICE.md`](NOTICE.md) for attribution and licensing notes.

## 5.7 Current limitation: Coding Agent repository synchronization

In v0.2, the normal executor path assumes that the Coding Agent works from a local checkout and synchronizes the canonical GitHub repository before execution:

```text
GitHub canonical repo
        ↓ git pull / fetch
local research checkout
        ↓
Coding Agent execution
```

This is simple and explicit, but it introduces friction:

- the local checkout can become stale;
- the Coding Agent must remember to sync before every new run;
- merge conflicts can interrupt the Fast Loop;
- the local working repository and the configured GitHub research repository may not always refer to the same source tree.

The agent instructions therefore currently require a sync check and escalation on unexpected divergence.

## 5.8 Roadmap: direct GitHub source access for Coding Agents

A future version should reduce the need for repeated manual/local synchronization.

The intended direction is:

```text
Current v0.2

GitHub
  ↓ pull
Local checkout
  ↓
Coding Agent


Possible future version

GitHub canonical source
  ↓ direct source / state access
Coding Agent
  ↓ execution workspace
results
  ↓
GitHub
```

The goal is for the Coding Agent to resolve the canonical source directly from GitHub when starting a run, rather than assuming that its current local checkout is already the correct and latest repository.

This still requires careful design around writable working trees, uncommitted local changes, reproducibility, and authentication.

## 5.9 Open compatibility question: Claude Code and repository identity

Another unresolved issue is repository identity when the Coding Agent's current working directory and the Research MCP's configured GitHub repository differ.

For example:

```text
Claude Code current workspace
        = local/project-A

Research MCP durable repo
        = github.com/user/project-B
```

Questions that need an explicit protocol include:

- Which repository is authoritative for source code?
- Should the Coding Agent refuse execution when local `origin` does not match the configured durable repository?
- Can the research-state repository and experiment-code repository intentionally be different?
- If they are different, how should commit SHAs and provenance link the two repositories?
- Should the MCP expose canonical repository identity to the Coding Agent before execution?

Until this is formalized, the safest v0.2 behavior is to treat repository mismatch or unexpected divergence as an escalation condition rather than guessing.

## 5.10 Status

**v0.2 prototype.** The local Git-backed protocol and self-hostable Research MCP are implemented. Interfaces may still change as repeated real-world research cycles reveal friction.

A stable `v1.0` should follow only after the protocol has been exercised through multiple complete planning → execution → analysis → critique cycles.

## 5.11 License

Research Loop is released under the MIT License. See [`LICENSE`](LICENSE).

Third-party inspiration and attribution are described in [`NOTICE.md`](NOTICE.md).
