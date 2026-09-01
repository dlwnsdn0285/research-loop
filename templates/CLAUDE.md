# Research Loop — Claude Instructions

Follow `RESEARCH_PROTOCOL.md`. The durable research record is under `research_runs_history/`, not in chat memory.

When planning, combine the current conversation with the latest completed run's `03_ANALYSIS.md` and `04_CRITIQUE.md` when available. For a new project with no completed run, use bootstrap planning from the current question and protocol. Explain a proposed plan and obtain approval before execution.

When executing, first sync the local checkout with the canonical GitHub branch. Summarize the latest approved/ready plan, wait for explicit approval when required, preserve raw outputs, validate them, register raw artifacts in the manifest, transition to `RESULTS_READY`, and commit/push successful execution results. Escalate validation failures, merge conflicts, destructive overwrites, or material deviations from the approved plan.

When analyzing, keep primary analysis and independent critique separate. Prefer different model/provider identities for `03_ANALYSIS.md` and `04_CRITIQUE.md`.

If Research MCP is connected, use it for durable state reads/writes and protocol transitions rather than editing research-state files ad hoc from chat. If Research Ponytail is enabled, apply it only to planning, analysis, critique, and next-step selection—not to raw-result recording.
