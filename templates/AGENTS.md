# Research Loop — Agent Instructions

This repository uses `RESEARCH_PROTOCOL.md` and `research_runs_history/` as the research workflow and source of truth.

## Always

- Read `RESEARCH_PROTOCOL.md` before handling a research run.
- Treat GitHub as the canonical durable state; sync the local checkout before starting execution.
- Do not mix experimental observations with interpretation.
- Do not execute a `PLAN_READY` run without explicit user approval.
- Do not rewrite raw results to make an interpretation cleaner.
- Do not write `03_ANALYSIS.md` or `04_CRITIQUE.md` while acting as executor.

## Executor workflow

When asked to run the latest experiment:

1. Fetch/pull the canonical branch and verify the local checkout is current. If a merge conflict or unexpected divergence exists, stop and escalate.
2. Find the latest run whose manifest status is `PLAN_READY` or `PLAN_APPROVED`.
3. Read its `00_MANIFEST.yaml` and `01_PLAN.md` and inspect the code needed to implement the plan.
4. Explain purpose, conditions, controls, metrics, implementation, commands, and expected artifacts.
5. Stop and request explicit approval if the plan is not already approved.
6. After approval, record approval, transition to `RUNNING`, execute the approved plan, and preserve raw outputs.
7. Run the planned validation/sanity checks. If validation fails or the plan must materially change, stop and escalate instead of inventing a new scientific direction.
8. Generate `02_RESULTS_RAW.md` from observed outputs without scientific interpretation.
9. Register retained raw artifact paths under `files.raw_results.artifacts` in `00_MANIFEST.yaml` and fill execution provenance such as commit, command, dataset/split, and seeds.
10. Validate the run, transition to `RESULTS_READY`, commit the run artifacts, and push them to the canonical GitHub branch.

A successful, approved execution path may commit and push automatically. Human escalation is required for validation failure, merge conflicts, destructive overwrite, or any material deviation from the approved plan.
