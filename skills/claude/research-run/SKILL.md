---
name: research-run
description: Execute the latest Research Loop experiment with a summary and explicit human approval gate.
---

# Research Run

Follow `RESEARCH_PROTOCOL.md` and `CLAUDE.md`. Locate the latest `PLAN_READY` or `PLAN_APPROVED` run, read its manifest and plan, inspect the implementation, and summarize purpose, conditions, controls, metrics, commands, and expected artifacts to the user. If approval is not recorded, stop and ask for explicit approval. After approval, execute the plan, preserve raw outputs, generate `02_RESULTS_RAW.md` without interpretation, validate, and set `RESULTS_READY` only when complete. Do not analyze the result while acting as executor.
