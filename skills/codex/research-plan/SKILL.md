---
name: research-plan
description: Propose the next Research Loop experiment from prior analysis and critique, explain it to the user, and commit only after explicit approval.
---

# Research Plan

1. Read `RESEARCH_PROTOCOL.md` and repository instructions.
2. Find the latest completed or critiqued run.
3. Read its `03_ANALYSIS.md`, `04_CRITIQUE.md`, relevant repository evidence/code, and the user's current request.
4. Draft the smallest experiment that can resolve the decision-relevant uncertainty. If Research Ponytail is enabled, apply it here.
5. Define conditions, controls, metrics, expected outcome branches, raw artifacts, and stop/expand rule before execution.
6. Explain the proposed plan to the user. Do not create or modify a run until the user explicitly approves if `before_plan_commit` is enabled.
7. After approval, create the next dated run with `00_MANIFEST.yaml` and `01_PLAN.md` and leave it at `PLAN_READY`.
