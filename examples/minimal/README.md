# Minimal example

After installing Research Loop, initialize it inside any research repository:

```bash
research-loop init .
research-loop new "does the baseline reproduce?"
```

This creates a dated run under `research_runs_history/`. Fill `01_PLAN.md`, obtain human approval, execute the experiment, preserve raw artifacts, and advance the run through the protocol.

A minimal first run should answer one narrow question, define a baseline/control, state the metric before execution, and specify what result would make further work unnecessary.
