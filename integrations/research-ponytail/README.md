# Research Ponytail integration

Research Loop and [Research Ponytail](https://github.com/dlwnsdn0285/research-ponytail) solve different problems:

- **Research Loop** controls state, provenance, artifact boundaries, and approval transitions.
- **Research Ponytail** controls reasoning complexity: identify the root uncertainty, reuse existing evidence, choose the smallest decisive test, and stop when the evidence threshold is met.

## Where the pairing helps

### Planning

Apply Research Ponytail while creating `01_PLAN.md` to avoid unnecessary experiment matrices and focus on the smallest test that can distinguish the live explanations.

### Analysis

Apply it while creating `03_ANALYSIS.md` to keep the conclusion proportional to the evidence and avoid expanding one result into an unsupported mechanism story.

### Critique and next-step selection

Apply it while creating `04_CRITIQUE.md` to prioritize the most credible failure mode and the single follow-up most likely to change the conclusion.

## Where it should not be applied

Do not use a reasoning policy to rewrite, filter, or reinterpret the raw-result layer. `raw/*` and `02_RESULTS_RAW.md` should record observations independently of Research Ponytail.

## Configuration

A project may document the optional policy in `research-loop.yaml`:

```yaml
reasoning:
  policy: research-ponytail
  mode: full
```

This setting is descriptive in v0.1: the local CLI does not install or invoke Research Ponytail automatically. Install the skill separately from its own repository and configure your agent/provider to use it during planning, analysis, and critique.
