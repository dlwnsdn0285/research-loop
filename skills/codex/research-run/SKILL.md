---
name: research-run
description: Execute the latest Research Loop experiment with a mandatory summary and human approval gate before running. Use when the user asks to run, execute, continue, or start the latest research experiment.
---

# Research Run

1. Read `RESEARCH_PROTOCOL.md` and `AGENTS.md`.
2. Find the latest run in `research_runs_history/` whose manifest status is `PLAN_READY` or `PLAN_APPROVED`.
3. Read `00_MANIFEST.yaml` and `01_PLAN.md` plus the code needed for implementation.
4. Before execution, explain the experiment purpose, conditions, controls, metrics, implementation plan, commands, and artifacts.
5. If explicit approval has not been recorded, stop and ask for it. Never infer approval from previous discussion.
6. After approval, update the manifest, run the experiment, save raw machine-readable outputs, and produce `02_RESULTS_RAW.md` without interpretation.
7. Register every retained raw artifact in `files.raw_results.artifacts` with `path`, `type`, and a factual `description` of what data the file contains. Do not put scientific conclusions in artifact descriptions.
8. Validate the run. Set `RESULTS_READY` only when required artifacts exist and the artifact registry is valid.
9. Do not create `03_ANALYSIS.md` or `04_CRITIQUE.md` while acting as executor.
