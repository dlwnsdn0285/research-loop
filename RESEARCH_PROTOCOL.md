# Research Protocol

Research Loop separates experimental evidence from interpretation and keeps durable research state in Git.

## Run layout

```text
research_runs_history/YYYY-MM-DD/expNN_slug/
├── 00_MANIFEST.yaml
├── 01_PLAN.md
├── 02_RESULTS_RAW.md
├── 03_ANALYSIS.md
├── 04_CRITIQUE.md
└── raw/
```

## States

```text
PLANNING → PLAN_READY → PLAN_APPROVED → RUNNING → RESULTS_READY → ANALYZED → CRITIQUED → COMPLETED
```

## Planner

The planner writes the research question, hypotheses, conditions, controls, metrics, expected outcome branches, stop/expand rule, and required raw artifacts before execution.

Material changes after results are known should become a new run rather than silently rewriting the old plan.

## Executor

Before execution, the executor reads the manifest and plan, summarizes the experiment to the user, and waits for explicit approval.

The executor records measurements and provenance only. Files under `raw/` and `02_RESULTS_RAW.md` should not contain interpretation such as “this supports” or causal explanations.

## Analyst

The analyst reads the frozen plan and observed results, maps results to predefined branches when possible, separates observations from inference, and writes `03_ANALYSIS.md`.

## Critic

The critic checks validity, leakage, implementation confounds, statistical weakness, alternative explanations, and overclaiming, then writes `04_CRITIQUE.md`.

## Source of truth

The Git repository is authoritative for research state. Chat history and model memory are supplementary context.

Preferred order for planning a follow-up:

1. previous `03_ANALYSIS.md`;
2. previous `04_CRITIQUE.md`;
3. repository evidence and code;
4. the user's current request;
5. chat/project memory as supplementary context.

## Raw result discipline

Prefer minimally transformed, machine-readable artifacts such as:

```text
raw/config.yaml
raw/metrics.json
raw/per_example.jsonl
raw/stdout.log
raw/run_commands.txt
raw/environment.txt
```

Projects may configure a smaller required set. Once `RESULTS_READY` is reached, raw outputs should normally be treated as immutable; corrections should be explicit.

## Provenance

`00_MANIFEST.yaml` should record available execution context such as run ID, parent run, status, approval metadata, branch, commit SHA, command, dataset/split, model/checkpoint identifiers, seeds, and artifact completeness.

## Optional reasoning policy

Research Loop does not prescribe a reasoning style. A policy such as Research Ponytail may guide planning, analysis, and critique, but it must never rewrite raw observations.
