# Research Loop — Agent Instructions

This repository uses `RESEARCH_PROTOCOL.md` and `research_runs_history/` as the research workflow and source of truth.

## Always

- Read `RESEARCH_PROTOCOL.md` before handling a research run.
- Treat `research_runs_history/` as durable research state.
- Do not mix experimental observations with interpretation.
- Do not execute a `PLAN_READY` run without explicit user approval.
- Do not rewrite raw results to make an interpretation cleaner.

## Executor workflow

When asked to run the latest experiment:

1. Find the latest run whose manifest status is `PLAN_READY` or `PLAN_APPROVED`.
2. Read its `00_MANIFEST.yaml` and `01_PLAN.md`.
3. Inspect the repository code needed to implement the plan.
4. Explain to the user: purpose, conditions, controls, metrics, implementation, commands, and expected artifacts.
5. Stop and request explicit approval if the plan is not already approved.
6. After approval, record approval, transition to `RUNNING`, execute the plan, and preserve raw outputs.
7. Generate `02_RESULTS_RAW.md` from observed outputs without scientific interpretation.
8. Validate the run and transition to `RESULTS_READY` when complete.

Do not write `03_ANALYSIS.md` or `04_CRITIQUE.md` while acting as executor unless the user explicitly switches your role.
