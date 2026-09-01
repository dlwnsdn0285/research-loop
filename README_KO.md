# Research Loop

[English README](README.md)

**LLM과 Coding Agent를 이용한 연구 자동화에서, 실행은 빠르게 자동화하되 연구적 판단은 사람이 이해하고 개입할 수 있도록 만든 Human-in-the-loop 연구 프로토콜입니다.**

> **실행은 자동화하고, Raw Result는 해석과 분리하며, 중요한 연구 판단은 사람과 Chat의 Slow Loop로 돌려보냅니다.**

---

# 1. 핵심 철학

LLM과 Coding Agent를 사용하면 실험 구현과 실행 속도는 매우 빨라집니다. 하지만 실험이 빨라질수록 연구자가 모든 결과를 이해하고, 오류를 발견하고, 다음 질문을 결정하는 것이 새로운 병목이 됩니다.

Research Loop은 이 문제를 다음 원칙으로 다룹니다.

## 1.1 Fast Loop와 Slow Loop를 분리한다

반복적이고 명확한 작업은 Coding Agent가 빠르게 처리합니다.

```text
Fast Loop

실험 구현
→ 실행
→ 재실행 / seed / sanity check
→ validation
→ raw result 저장
```

반면 결과의 의미를 해석하거나 다음 연구 방향을 결정하는 작업은 사람이 참여하는 Slow Loop로 보냅니다.

```text
Slow Loop

결과 이해
→ 질문
→ 반박 / 토론
→ 가설 수정
→ 다음 실험 결정
```

즉,

> **실행은 자동화하고, 불확실한 연구 판단은 사람에게 돌려보냅니다.**

## 1.2 Coding Agent와 Chat을 분리한다

Coding Agent와 ChatGPT/Claude가 비슷한 기반 모델을 사용하더라도 실제 사용 환경, 즉 **harness**는 다릅니다.

```text
Coding Agent
→ 코드 수정 / 실행 / 디버깅에 적합

Chat
→ 설명 / 질문 / 토론 / 의사결정에 적합
```

따라서 Research Loop에서는 다음처럼 역할을 분리합니다.

- **Coding Agent = 실행**
- **Chat = 사람과 함께 reasoning**

Coding Agent가 만든 결과에 바로 해석을 붙이지 않고 **Raw Result**로 보존한 뒤, Chat과 사람이 함께 그 결과를 해석합니다.

## 1.3 Raw Result와 Inference를 분리한다

LLM의 해석은 유용하지만 틀릴 수 있습니다. 특히 이전 LLM의 해석을 다음 LLM이 다시 요약하고 사용하는 과정이 반복되면 작은 오류가 점점 사실처럼 누적될 수 있습니다.

```text
실험 결과
   ↓
RAW RESULT
   ↓
사람 + Chat
   ↓
ANALYSIS
   ↓
독립적인 CRITIQUE
```

따라서 **관측된 사실과 그 사실에 대한 해석을 서로 다른 artifact로 보존**합니다.

- `raw/*`, `02_RESULTS_RAW.md` = observation
- `03_ANALYSIS.md` = primary inference
- `04_CRITIQUE.md` = independent/adversarial inference

## 1.4 Human-in-the-loop을 단순 승인 버튼으로 사용하지 않는다

일반적인 Human-in-the-loop은 종종 다음처럼 동작합니다.

```text
Agent 제안
   ↓
사람
Approve / Reject
```

이 방식은 사람이 이미 문제를 충분히 이해하고 있을 때 가장 잘 작동합니다.

Research Loop에서는 Chat을 Slow Loop interface로 사용합니다.

```text
Raw Result
   ↓
Chat 설명
   ↓
Human 질문
   ↓
토론 / 반박
   ↓
공유된 이해
   ↓
Human Decision
```

즉, 사람이 단순히 결과에 동의/비동의하는 것이 아니라 **해석이 만들어지는 과정 자체에 참여**합니다.

최종 analysis나 plan이 저장될 때 reasoning client는 다음 두 context를 함께 사용합니다.

```text
CURRENT CHAT CONTEXT
        +
DURABLE GITHUB STATE
        ↓
research inference
```

## 1.5 Provenance를 보존한다

Research Loop는 최신 결론만 남기지 않습니다. 각 run은 parent experiment, plan, raw result, analysis, critique, author/provider, state transition을 보존합니다.

```text
Experiment 1
    ↓
Experiment 2
    ↓
Experiment 3
```

새로운 결과가 이전 해석을 뒤집더라도 과거 analysis를 덮어쓰지 않습니다. 대신 다음 run에서 **왜 판단이 바뀌었는지**를 남깁니다.

따라서 repository는 단순히 최신 결론을 보관하는 곳이 아니라 **uncertainty가 어떻게 줄어들었는지에 대한 기록**이 됩니다.

## 1.6 Research State는 LLM이 아니라 MCP가 관리한다

LLM은 연구에 대해 reasoning하지만, research protocol을 임의로 바꾸지는 않습니다.

```text
LLM
 │
 │ "analysis 저장"
 ▼
Research MCP
 │
 ├─ 현재 상태가 RESULTS_READY인가?
 ├─ 기존 analysis가 있는가?
 ├─ provenance가 올바른가?
 └─ 허용된 transition인가?
 │
 ▼
GitHub
```

즉,

> **LLM은 판단하고, MCP는 protocol을 집행합니다.**

State machine은 다음과 같습니다.

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

## 1.7 ChatGPT와 Claude의 역할 분리

Research Loop 자체는 provider-independent합니다. 다만 이 repository를 만들면서 얻은 **operational heuristic**은 다음과 같습니다.

```text
ChatGPT
  └─ 비교적 넓고 가볍게 탐색
     └─ 이해하기 쉬운 설명
        └─ 초기 planning / primary analysis에 유용

Claude
  └─ 비교적 좁고 깊게 검토
     └─ assumptions를 강하게 의심
        └─ independent critique에 유용
```

따라서 기본 사용 예시는 다음과 같습니다.

```text
Human + ChatGPT → plan / primary analysis
Claude          → independent critique
```

이는 보편적인 모델 성능 주장이 아니라 실제 사용 경험에 기반한 역할 분리입니다. 핵심은 특정 provider가 아니라 **primary analysis와 critique가 충분히 독립적이어야 한다는 점**입니다.

---

# 2. 실제 구성

```text
                    Human
                      │
              질문 / 이해 / 결정
                      │
          ┌───────────┴───────────┐
          ▼                       ▼
      ChatGPT                   Claude
  Planning / Analysis           Critique
          │                       │
          └───────────┬───────────┘
                      ▼
                 Research MCP
             Protocol / State Layer
                      │
                      ▼
                    GitHub
              Source of Truth
                      ▲
                      │ pull / push
                      │
                Coding Agent
             Experiment Execution
```

| Component | 역할 |
|---|---|
| **Human** | 최종 연구 판단 |
| **ChatGPT** | 초기 planning, 설명, primary analysis |
| **Claude** | 독립적인 critique |
| **Coding Agent** | 코드 구현, 실험 실행, validation |
| **Research MCP** | semantic operation, 상태 변경, protocol 검증 |
| **GitHub** | durable research state / provenance / Source of Truth |

## 2.1 Run 구조

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

```text
Run
├─ Manifest        → identity / state / provenance / artifact registry
├─ Plan            → pre-result hypotheses and decision branches
├─ Raw Results     → observations only
├─ Analysis        → primary interpretation
└─ Critique        → independent adversarial review
```

전체 protocol은 [`RESEARCH_PROTOCOL.md`](RESEARCH_PROTOCOL.md)를 참고하세요.

## 2.2 Research MCP의 10개 semantic tool

| Phase | Tool | 역할 |
|---|---|---|
| State | `get_research_status` | 현재 deterministic loop state 읽기 |
| State | `get_latest_run` | 특정 상태의 최신 run 찾기 |
| Planning | `load_planning_context` | 이전 durable context와 protocol 불러오기 |
| Planning | `create_planned_run` | Chat에서 확정된 plan을 `PLAN_READY`로 저장 |
| Analysis | `load_analysis_context` | plan, raw summary, artifact inventory 로드 |
| Analysis | `read_run_file` | 필요한 raw/text evidence 직접 확인 |
| Analysis | `save_analysis` | `03_ANALYSIS.md` 저장 및 `ANALYZED` 전환 |
| Critique | `load_critique_context` | 독립 critique용 context 로드 |
| Critique | `save_critique` | `04_CRITIQUE.md` 저장 및 `CRITIQUED` 전환 |
| Completion | `complete_run` | invariants 검증 후 `COMPLETED` 전환 |

Research MCP는 자체적으로 hypothesis를 고르거나 scientific conclusion을 생성하지 않습니다.

---

# 3. 실제 Workflow

하나의 연구 cycle은 다음처럼 진행됩니다.

```text
             ┌──────────────────────┐
             │      SLOW LOOP       │
             │                      │
             │ Human + ChatGPT      │
             │ 결과 이해 / 질문      │
             │ 다음 실험 설계        │
             └──────────┬───────────┘
                        │
                   PLAN_READY
                        │
                        ▼
             ┌──────────────────────┐
             │      FAST LOOP       │
             │                      │
             │ Coding Agent         │
             │ 구현 → 실행           │
             │ → validation         │
             │ → raw result         │
             └──────────┬───────────┘
                        │
                  RESULTS_READY
                        │
                        ▼
             ┌──────────────────────┐
             │      SLOW LOOP       │
             │                      │
             │ ChatGPT Analysis     │
             │        ↓             │
             │ Claude Critique      │
             │        ↓             │
             │ Human Decision       │
             └──────────┬───────────┘
                        │
                    COMPLETED
                        │
                        ▼
                 Next Experiment
```

Artifact 기준으로 보면 다음과 같습니다.

```text
01_PLAN.md
     ↓
Human approval
     ↓
Coding Agent
     ↓
raw/* + 02_RESULTS_RAW.md
     ↓
ChatGPT + Human
     ↓
03_ANALYSIS.md
     ↓
Claude
     ↓
04_CRITIQUE.md
     ↓
Human Decision
     ↓
COMPLETED
     ↓
다음 Run의 parent
```

## 한 문장으로 요약하면

> **Research Loop은 Coding Agent에게 반복적인 실험 실행을 맡기고, Raw Result를 해석과 분리하여 보존하며, Chat과 Human이 Slow Loop에서 결과를 충분히 이해하고 토론한 뒤 연구 판단을 내리도록 하는 GitHub + MCP 기반 Human-in-the-loop 연구 프로토콜입니다.**

---

# 4. 설치 및 사용 방법

## 4.1 Local protocol만 사용

```bash
git clone https://github.com/dlwnsdn0285/research-loop.git
cd research-loop
python -m pip install -e .
```

기존 연구 repository 안에 초기화합니다.

```bash
research-loop init /path/to/your-project
```

필요하면 local run을 직접 만들 수 있습니다.

```bash
cd /path/to/your-project
research-loop new "baseline sanity check"
research-loop validate --all
```

이 local mode에서는 MCP가 필요하지 않습니다.

## 4.2 Research MCP 추가

```bash
python -m pip install -e '.[mcp]'
```

자신의 research repository를 지정합니다.

```bash
export RESEARCH_GITHUB_REPO=YOUR_GITHUB_USER/YOUR_RESEARCH_REPO
export GITHUB_TOKEN=YOUR_FINE_GRAINED_GITHUB_TOKEN
export RESEARCH_GITHUB_BRANCH=main
research-mcp
```

Local Streamable HTTP 테스트:

```bash
research-mcp --transport streamable-http --host 127.0.0.1 --port 8000
```

MCP endpoint는 `/mcp`, liveness endpoint는 `/healthz`입니다.

## 4.3 Remote / self-hosted MCP

권장 구조는 **각 researcher/project가 자신의 MCP deployment와 GitHub credential을 소유하는 방식**입니다.

```text
ChatGPT / Claude
      ↓ HTTPS + OAuth/OIDC
Self-hosted Research MCP
      ↓ repo-scoped GitHub credential
Your research repository
      ↑ git push / pull
Coding Agent
```

사용할 파일:

- [`Dockerfile.research-mcp`](Dockerfile.research-mcp)
- [`cloudbuild.research-mcp.yaml`](cloudbuild.research-mcp.yaml)
- [`research_mcp/.env.remote.example`](research_mcp/.env.remote.example)

Google Cloud Run 예시는 [`research_mcp/CLOUD_RUN.md`](research_mcp/CLOUD_RUN.md)를 참고하세요.

---

# 5. 사용 예시

사용자는 MCP API 이름보다 **연구 언어로 대화하는 것**이 기본입니다.

### 1) 현재 연구 상태 확인

> 현재 research status가 어떻게 돼?

내부적으로 reasoning client가 `get_research_status()`를 호출할 수 있지만 사용자가 tool 이름을 기억할 필요는 없습니다.

### 2) 다음 실험 논의

> 이전 결과와 critique를 바탕으로 다음 실험을 정해보자. 다만 더 엄격한 control에서도 현상이 유지되는지 보고 싶어.

```text
load_planning_context()
        +
current conversation
        ↓
Human + ChatGPT discussion
        ↓
final experiment plan
        ↓
create_planned_run(...)
        ↓
PLAN_READY
```

### 3) Coding Agent 실행

```text
sync latest GitHub state
        ↓
read plan
        ↓
explain implementation
        ↓
request approval
        ↓
execute + validate
        ↓
raw/config, raw/metrics, logs ...
        ↓
02_RESULTS_RAW.md
        ↓
RESULTS_READY
        ↓
commit + push
```

### 4) Chat에서 primary analysis

> 최신 결과를 분석해줘. 중요한 주장은 raw artifact까지 확인하고, 내가 이해할 수 있게 설명해줘.

```text
load_analysis_context()
        ↓
read_run_file(...) when needed
        ↓
conversation with human
        ↓
03_ANALYSIS.md
```

### 5) Independent critique

기본 예시는 다음과 같습니다.

```text
ChatGPT → primary analysis
Claude  → critique
```

Critic은 assumptions, confounders, fairness, overclaiming, alternative explanation 등을 다시 검토합니다.

### 6) Human judgment 및 completion

```text
CRITIQUED
    ↓
Human judgment
    ↓
complete_run()
    ↓
COMPLETED
```

다음 planning cycle은 이 run을 parent provenance로 사용합니다.

---

# 6. 추가 내용 / Warning / Roadmap

## Warning: 모델 역할은 heuristic이다

ChatGPT-planner / Claude-critic 역할 분리는 실제 사용 경험에 기반한 heuristic이며 보편적인 benchmark claim이 아닙니다. 환경에 맞게 충분히 독립적인 provider/model을 사용하세요.

## Warning: Research MCP는 scientific agent가 아니다

Research MCP는 다음을 하지 않습니다.

- 다음 research question 발명;
- competing explanation 중 하나 선택;
- plan을 임의 수정;
- raw result를 causal claim으로 변환;
- surprising result를 이유로 새로운 연구 방향 결정.

이 판단은 Slow Loop에 속합니다.

## Warning: Raw Result는 raw여야 한다

Executor가 `02_RESULTS_RAW.md`를 선호하는 해석에 맞춰 설득력 있게 고쳐서는 안 됩니다. Raw artifact는 최소한으로 변형되고 재현 가능해야 합니다.

## Warning: Remote MCP는 실제 보안 경계가 필요하다

인증이 꺼진 HTTP mode를 public internet에 노출하지 마세요.

권장 사항:

- HTTPS;
- OAuth/OIDC;
- repo-scoped GitHub credential;
- Secret Manager를 통한 token injection;
- multi-tenant isolation을 따로 구현하지 않는다면 researcher/project별 MCP deployment.

## Optional: Research Ponytail

Research Loop은 **research state와 provenance**를 관리하고, [Research Ponytail](https://github.com/dlwnsdn0285/research-ponytail)은 **research complexity**를 관리합니다.

```text
Research Ponytail decides what is worth testing.
Research Loop remembers what was actually tested.
```

Research Ponytail은 planning, analysis, critique, next-step selection에 사용하기 적합하며 raw-result layer에는 개입하지 않습니다.

## Inspiration: LLM Wiki

Research Loop은 Andrej Karpathy의 **LLM Wiki** idea file에서 일부 영감을 받았습니다.

https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f

핵심적으로 transient conversation 대신 filesystem artifact에 durable state를 두고, source material과 LLM-derived material을 구분하는 일반적인 아이디어에서 영감을 받았습니다.

Research Loop은 이를 computational experiment lifecycle에 적용하여 plan, human approval, raw-result isolation, analysis, critique, state, provenance를 추가합니다.

LLM Wiki gist의 text나 code를 복사하여 포함하지 않았습니다. 자세한 attribution은 [`NOTICE.md`](NOTICE.md)를 참고하세요.

## 현재 한계: Coding Agent repository synchronization

v0.2의 일반적인 executor path에서는 Coding Agent가 local checkout에서 작업하며 실행 전에 canonical GitHub repository를 동기화합니다.

```text
GitHub canonical repo
        ↓ git pull / fetch
local research checkout
        ↓
Coding Agent execution
```

따라서 local checkout stale, merge conflict, repository mismatch 등의 friction이 존재합니다.

## Roadmap: Coding Agent의 direct GitHub source access

향후에는 매번 local `git pull`을 전제로 하기보다 Coding Agent가 실행 시작 시 canonical GitHub source를 직접 resolve하는 방향을 고려합니다.

```text
Current v0.2
GitHub → pull → Local checkout → Coding Agent

Future direction
GitHub canonical source → Coding Agent execution workspace → results → GitHub
```

다만 writable working tree, uncommitted changes, authentication, reproducibility에 대한 명확한 protocol이 필요합니다.

## Open question: Claude Code와 repository identity

예를 들어 다음처럼 Coding Agent의 workspace와 Research MCP가 가리키는 repository가 다를 수 있습니다.

```text
Claude Code current workspace
        = local/project-A

Research MCP durable repo
        = github.com/user/project-B
```

아직 명확히 정해야 할 문제:

- 어느 repository가 source code의 authoritative source인가?
- local `origin`과 durable repo가 다르면 실행을 거부해야 하는가?
- research-state repo와 experiment-code repo를 의도적으로 분리할 수 있는가?
- 분리한다면 commit SHA와 provenance를 어떻게 연결할 것인가?
- MCP가 실행 전에 canonical repository identity를 Coding Agent에게 제공해야 하는가?

현재 v0.2에서는 repository mismatch나 unexpected divergence를 **추측해서 처리하지 않고 escalation condition으로 보는 것**이 가장 안전합니다.

## Status

**v0.2 prototype.** Local Git-backed protocol과 self-hostable Research MCP가 구현되어 있습니다. 반복적인 실제 end-to-end 연구 cycle을 통해 interface는 변경될 수 있습니다.

Stable `v1.0`은 여러 번의 planning → execution → analysis → critique cycle을 거친 이후를 목표로 합니다.

## License

Research Loop은 MIT License로 배포됩니다. [`LICENSE`](LICENSE)를 참고하세요.

Third-party inspiration 및 attribution은 [`NOTICE.md`](NOTICE.md)에 정리되어 있습니다.
