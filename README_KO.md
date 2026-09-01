# Research Loop

[English README](README.md)

**추적 가능하고 human-in-the-loop인 LLM 보조 연구를 위한, 선택적 MCP 상태 계층을 포함한 Git 기반 연구 프로토콜.**

Research Loop는 LLM 채팅, Coding Agent, 반복적인 실험이 함께 사용되는 연구를 위한 경량 워크플로우입니다. 현재의 채팅 세션이나 가장 최근 Agent의 해석이 사실상의 source of truth가 되도록 두는 대신, 지속적으로 보존되어야 할 과학적 기록을 Git에 남깁니다.

핵심 아이디어는 단순합니다.

> **Evidence, interpretation, research state, human decision은 서로 구분되어야 합니다.**

---

# 1. 철학

## 1.1 왜 이 구조가 필요한가

LLM은 연구 전반에서 유용합니다. 가설을 제안하고, 실험을 설계하고, 코드를 작성하고, 결과를 확인하고, 실패를 설명하고, 다음 단계를 제안할 수 있습니다. 하지만 장기적인 연구에서는 이런 역할들이 쉽게 서로 뒤섞입니다.

하나의 자동 생성 리포트 안에는 조용히 다음 내용들이 섞일 수 있습니다.

- 실험에서 실제로 측정된 값;
- 결과를 본 뒤 선택된 예시;
- 측정값에 대한 해석;
- 직접 검증되지 않은 인과 설명;
- 다음 실험에 대한 제안.

그 다음 모델은 이 리포트를 context로 읽게 되고, 한 iteration에서 만들어진 inference가 다음 iteration에서는 점차 사실처럼 취급될 수 있습니다. 동시에 Coding Agent는 매우 빠르게 새로운 실험을 계속 만들어낼 수 있기 때문에, 사람이 무엇이 바뀌었는지, 왜 바뀌었는지, 무엇을 추가로 의심해야 하는지를 충분히 이해하는 속도보다 실험 진행 속도가 더 빨라질 수 있습니다.

Research Loop는 바로 이 병목을 중심으로 설계되었습니다.

> **Automation은 사람이 이해하고 follow-up할 수 있는 속도보다 훨씬 빠르게 실험을 진행시킬 수 있습니다.**

따라서 목표는 완전히 자율적인 research agent를 만드는 것이 아닙니다. 반복적인 실행은 자동화하되, researcher가 evidence를 이해하고, 의심하고, 질문하고, 최종적으로 무엇을 의미하는지 결정할 수 있는 느린 reasoning interface를 함께 유지하는 것이 목표입니다.

```text
                 FAST LOOP
             machine-side 실행
                    │
                    │ produces
                    ▼
              RAW EVIDENCE
                    │
                    │ 해석이 필요해지면
                    │ escalation
                    ▼
                 SLOW LOOP
          human + conversational LLM
                    │
           이해 → 질문 → 토론
                    │
                    ▼
              HUMAN CONSENSUS
                    │
                    ▼
                next experiment
```

## 1.2 Fast Loop과 Slow Loop

Research Loop는 의도적으로 서로 다른 두 속도의 작업을 분리합니다.

### Fast Loop — machine-side execution

대표적인 Fast Loop 작업은 다음과 같습니다.

- 최신 canonical GitHub state 동기화;
- 승인된 plan 구현;
- 실험 실행;
- 실패한 run 재실행;
- 고정된 seed 추가;
- metric aggregation;
- baseline reproduction;
- 사전에 정해진 ablation;
- sanity check;
- raw output과 execution provenance 보존;
- 성공한 run validation;
- 결과를 `RESULTS_READY` 상태로 commit/push.

이 작업들은 대체로 명시적이고, 반복적이며, machine-facing입니다.

### Slow Loop — epistemic decision

Slow Loop는 다음과 같은 질문을 다룹니다.

- 이 결과가 실제로 정당화하는 결론은 어디까지인가?
- 아직 가능한 competing explanation은 무엇인가?
- 이 결과가 현재 working hypothesis를 바꾸기에 충분히 강한가?
- 현재 uncertainty를 실질적으로 줄일 수 있는 가장 작은 다음 실험은 무엇인가?
- 현재 method story가 과도하게 주장하고 있지는 않은가?
- 이 연구는 계속해야 하는가, pivot해야 하는가, 멈춰야 하는가?

의도된 escalation rule은 단순합니다.

> **Execution은 자동화하고, scientific uncertainty는 escalation합니다.**

Slow Loop는 단순한 승인 창이 아닙니다. Conversational model은 researcher가 현재 상태를 이해할 수 있도록 설명하고, 낯선 세부사항을 풀어서 설명하고, follow-up 질문에 답하고, 해석을 반박하거나 비교하면서 researcher가 충분히 이해한 상태에서 결정을 내릴 수 있도록 돕습니다.

## 1.3 왜 conversational chat과 Coding Agent를 분리하는가

Coding Agent와 chat product는 동일하거나 유사한 underlying model family를 사용할 수 있습니다. 하지만 둘은 서로 다른 **harness** 안에서 동작합니다.

Coding-agent harness는 work에 최적화되어 있습니다.

- repository 탐색;
- 파일 수정;
- 명령어 실행;
- debugging;
- 반복 실행;
- machine state 조작.

Conversational-chat harness는 사람과의 상호작용에 최적화되어 있습니다.

- 설명;
- 반복적인 질문과 답변;
- 관점 재구성;
- 반박;
- 서로 다른 해석 비교;
- 사용자가 충분히 이해하고 판단할 수 있을 때까지 토론 유지.

따라서 Research Loop는 underlying model이 유사하더라도 둘을 서로 다른 interface로 취급합니다.

```text
                 Human researcher
                       │
               conversational interface
                       │
                이해 / challenge
                       │
                       ▼
                 ChatGPT / Claude
                 reasoning interface
                       │
                       │ semantic operation
                       ▼
                  Research MCP
                       │
                       ▼
                     GitHub
               durable source of truth
                       ▲
                       │ git pull / push
                       │
                  Coding Agent
                execution interface
```

Coding Agent는 executor로 행동하는 동안 공식적인 scientific interpretation과 의도적으로 분리됩니다. Coding Agent의 역할은 **무슨 일이 있었는지 기록하는 것**이지, 그 결과를 하나의 이야기로 만드는 것이 아닙니다.

## 1.4 Raw result와 inference는 서로 다른 artifact이다

Research Loop는 observation과 interpretation을 분리합니다.

```text
01_PLAN.md
    ↓ human approval
experiment
    ↓
raw/* + 02_RESULTS_RAW.md   ← observation
    ↓
03_ANALYSIS.md              ← inference
    ↓ independent review
04_CRITIQUE.md              ← adversarial inference
    ↓
COMPLETED
```

Executor는 `raw/` 아래에 파일을 기록하고 `02_RESULTS_RAW.md`를 생성할 수 있지만, 이 artifact들은 observational해야 합니다. 예를 들어 “이 결과가 증명한다”, “이 결과는 메커니즘이 X라는 것을 시사한다”, “다음 실험은 Y여야 한다”와 같은 해석을 몰래 포함해서는 안 됩니다.

Interpretation은 `03_ANALYSIS.md`와 `04_CRITIQUE.md`에 속합니다.

이 구분이 중요한 이유는 사람이 읽을 수 있는 inference는 유용하지만 fallible하기 때문입니다. Inference가 반복해서 요약되고, 압축되고, 다른 Agent에게 전달되면 오류가 누적될 수 있습니다. 원래의 measurement를 별도로 보존하면 다른 모델, 혹은 몇 달 뒤의 동일한 researcher가 이전 설명을 measurement처럼 물려받지 않고 동일한 evidence를 다시 해석할 수 있습니다.

## 1.5 Human-in-the-loop은 binary gate가 아니라 conversation이다

많은 human-in-the-loop 시스템은 사람을 매우 좁은 decision point에 배치합니다.

```text
agent proposes action
       ↓
 human: approve / reject
```

사람이 이미 충분한 전문지식과 context를 갖고 있다면 이 방식은 잘 작동할 수 있습니다. 하지만 장기 연구에서는 사람이 먼저 **왜 이 결정이 중요한지 이해해야 한다는 것 자체가 병목**인 경우가 많습니다.

Research Loop는 conversational chat을 Slow Loop의 interface로 사용합니다.

```text
raw evidence
    ↓
chat이 현재 상태 설명
    ↓
human이 기초적인 질문 또는 전문적인 질문
    ↓
chat이 답변 / 반박 / alternative 비교
    ↓
shared working understanding
    ↓
human decision
```

따라서 researcher는 inference가 durable research state가 되기 전에 개입할 수 있습니다. Conversation에는 GitHub에 아직 기록되지 않은 correction, doubt, 새로운 constraint, 새로운 question이 포함될 수 있습니다. Analysis나 다음 plan이 최종적으로 저장될 때 reasoning client는 다음 두 context를 결합합니다.

```text
CURRENT CHAT CONTEXT
        +
DURABLE GITHUB STATE
        ↓
research inference
```

이 구조에서 사람의 역할은 단순한 승인 버튼보다 훨씬 넓습니다. 사람은 **해석이 만들어지는 과정 자체에 참여**할 수 있습니다.

## 1.6 Provenance: 결론이 어떻게 바뀌었는지를 보존한다

Research Loop는 가장 최신 결론만 남기지 않습니다.

각 run은 다음을 보존합니다.

- parent experiment;
- 실험 실행 전 plan;
- raw result;
- primary analysis;
- independent critique;
- author/provider provenance;
- state transition.

나중의 실험이 이전 해석을 뒤집을 수 있습니다. 이 경우 이전 analysis를 삭제하고 마치 처음부터 틀리지 않았던 것처럼 다시 작성하지 않습니다. 대신 다음 run에서 **왜 해석이 바뀌었는지**를 기록합니다.

따라서 repository는 단순히 가장 최근 story를 담는 폴더가 아니라, **uncertainty가 어떻게 줄어들었는지에 대한 역사**가 됩니다.

## 1.7 왜 MCP가 state machine을 제어하는가

LLM은 research reasoning을 해야 하지만, research protocol 자체를 자유롭게 바꾸어서는 안 됩니다.

따라서 Research Loop는 각 reasoning client가 protocol file을 임의로 직접 수정하도록 두는 대신, Research MCP를 통해 semantic operation을 제공합니다.

```text
Reasoning client
      │
      │ "save analysis"
      ▼
Research MCP
      │
      ├─ run이 RESULTS_READY인가?
      ├─ analysis가 이미 존재하는가?
      ├─ provenance가 유효한가?
      └─ 다음 state transition이 허용되는가?
      │
      ▼
GitHub
```

이는 모든 client가 database file을 직접 수정하도록 두는 대신 transaction/API를 사용하는 것과 유사합니다.

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

`RESULTS_READY`는 observation은 존재하지만 공식 interpretation은 아직 없다는 뜻입니다. `ANALYZED`는 primary analysis가 존재하지만 independent critique를 아직 받지 않았다는 뜻입니다. `COMPLETED`는 다음 planning cycle의 durable parent로 안전하게 사용할 수 있는 상태입니다.

## 1.8 왜 planning에는 ChatGPT, critique에는 Claude인가

Research Loop는 provider-independent합니다. ChatGPT, Claude, 또는 다른 충분히 capable한 model이 어떤 reasoning role이든 맡을 수 있습니다.

다만 이 repository를 만들게 된 실제 workflow에서는 저자의 사용 경험에 기반한 다음과 같은 **operational heuristic**을 사용했습니다. 이것은 모델 전체에 대한 보편적인 성능 주장이나 benchmark claim이 아닙니다.

```text
ChatGPT
  └─ 비교적 broad / light한 exploration
     └─ 따라가기 쉬운 설명
        └─ human과 함께 초기 planning하기에 유용

Claude
  └─ 비교적 narrow / deep한 inspection
     └─ assumption을 공격적으로 점검
        └─ independent critique에 유용
```

따라서 유용한 기본값은 다음과 같습니다.

```text
Human + ChatGPT → plan / primary interpretation
Claude          → independent critique
```

정확히 어떤 provider를 쓰는지가 핵심은 아닙니다. 중요한 것은 primary interpretation과 adversarial review가 의미 있게 독립적이어야 한다는 점입니다.

Research MCP는 normal completion path에서 동일한 analysis/critique author identity를 거부함으로써 이 원칙의 최소한을 강제합니다.

## 1.9 Design principles

1. **GitHub/Git은 durable state이다.** Chat과 Agent는 기록 자체가 아니라 기록을 사용하는 client이다.
2. **Observed information과 inferred information은 서로 다른 artifact이다.**
3. **Plan은 그 plan이 해석하려는 result보다 먼저 존재해야 한다.**
4. **Raw output은 가능한 한 minimally transformed하고 reproducible해야 한다.**
5. **중요한 execution에는 human approval이 first-class gate로 존재한다.**
6. **Slow Loop는 사람에게 결정을 요구하기 전에 먼저 이해할 수 있도록 도와야 한다.**
7. **Coding-agent execution과 conversational inference는 의도적으로 분리한다.**
8. **Reasoning client는 ad hoc filesystem mutation 대신 하나의 protocol을 공유한다.**
9. **Independent critique는 primary analysis를 challenge해야 한다.**
10. **Automation은 bookkeeping을 줄이되 scientific accountability를 제거하지 않는다.**
11. **이전 해석을 덮어쓰기보다 provenance를 보존한다.**
12. **현재 uncertainty를 실질적으로 줄일 수 있는 가장 작은 실험을 우선한다.**

---

# 2. 실제 구성

## 2.1 Component와 역할

```text
                Human Researcher
                       │
          ┌────────────┴────────────┐
          │                         │
     ChatGPT Chat               Claude Chat
   planning / analysis        independent critique
          │                         │
          └──────────┬──────────────┘
                     ▼
                Research MCP
             protocol / state layer
                     │
                     ▼
                   GitHub
          durable research source of truth
                     ▲
                     │ git pull / push
                     │
                Coding Agent
              execution on lab/GPU
```

### Human Researcher — 최종 decision authority

사람은 다음을 결정합니다.

- 어떤 scientific claim을 신뢰할지;
- 어떤 explanation이 plausible한지;
- 추가 실험이 필요한지;
- 다음에 어떤 실험을 수행할 가치가 있는지;
- 결론을 얼마나 강하게 주장할 수 있는지.

### ChatGPT / Claude — interactive reasoning layer

Chat model은 다음을 수행합니다.

- hypothesis 생성 및 비교;
- evidence 설명;
- experiment design;
- result interpretation;
- assumption challenge;
- researcher와 uncertainty 토론.

이들은 현재 conversation과 Research MCP를 통해 불러온 durable state를 함께 사용합니다.

### Research MCP — protocol / persistence layer

Research MCP는 **scientific reasoning을 수행하지 않습니다.** 대신 다음을 수행합니다.

- durable research state 읽기;
- 허용된 semantic operation 제공;
- 이미 작성된 plan, analysis, critique 저장;
- state transition 검증;
- provenance와 completion invariant 강제.

### GitHub — durable state / provenance layer

GitHub는 versioned research record를 저장합니다.

- plan;
- manifest/state;
- raw results;
- analysis;
- critique;
- provenance;
- experiment lineage.

### Coding Agent — execution layer

Coding Agent는 다음을 수행합니다.

- 최신 repository state 동기화;
- 승인된 plan 읽기;
- experiment 구현 및 실행;
- validation과 sanity check 수행;
- raw result와 log 기록;
- execution provenance 업데이트;
- 성공한 run을 `RESULTS_READY` 상태로 commit/push.

Executor로 행동하는 동안 다음 scientific hypothesis를 독립적으로 선택해서는 안 됩니다.

## 2.2 Run structure

각 run은 날짜 기반 history directory 아래에 위치합니다.

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

개념적으로는 다음과 같습니다.

```text
Run
├─ Manifest        → identity / state / provenance / artifact registry
├─ Plan            → pre-result hypotheses and decision branches
├─ Raw Results     → observations only
├─ Analysis        → primary interpretation
└─ Critique        → independent adversarial review
```

전체 contract는 [`RESEARCH_PROTOCOL.md`](RESEARCH_PROTOCOL.md)를 참고하세요.

## 2.3 Research MCP의 10개 tool

| Phase | Tool | 역할 |
|---|---|---|
| State | `get_research_status` | deterministic loop state 읽기 |
| State | `get_latest_run` | 특정 status의 가장 최근 run 찾기 |
| Planning | `load_planning_context` | durable prior context + protocol 불러오기 |
| Planning | `create_planned_run` | chat에서 작성한 plan을 `PLAN_READY`로 저장 |
| Analysis | `load_analysis_context` | plan, raw summary, artifact inventory 불러오기 |
| Analysis | `read_run_file` | 필요한 raw/text evidence를 선택적으로 확인 |
| Analysis | `save_analysis` | `03_ANALYSIS.md` 저장 후 `ANALYZED`로 transition |
| Critique | `load_critique_context` | independent-review context 불러오기 |
| Critique | `save_critique` | `04_CRITIQUE.md` 저장 후 `CRITIQUED`로 transition |
| Completion | `complete_run` | invariant를 검증한 뒤 `COMPLETED`로 transition |

MCP 자체는 hypothesis를 선택하거나 scientific conclusion을 생성하지 않습니다.

이전 `COMPLETED` run이 없는 완전히 새로운 project에서도 첫 plan을 만들 수 있습니다.

## 2.4 Coding Agent contract

정상적인 성공 경로는 다음과 같습니다.

```text
sync canonical GitHub state
        ↓
read PLAN_READY / PLAN_APPROVED run
        ↓
explain execution + obtain approval
        ↓
RUNNING
        ↓
execute + validate
        ↓
preserve raw artifacts
        ↓
02_RESULTS_RAW.md + manifest provenance
        ↓
RESULTS_READY
        ↓
commit + push
```

`research-loop init`으로 생성되는 `AGENTS.md`와 `CLAUDE.md`가 이 executor boundary를 정의합니다.

Coding Agent는 다음 상황에서 멈추고 escalation해야 합니다.

- validation 실패;
- merge conflict 또는 예상하지 못한 divergence;
- 기존 raw artifact를 destructive overwrite해야 하는 상황;
- 승인된 experimental design을 materially 변경해야 하는 상황;
- 단순 retry가 아니라 새로운 scientific decision이 필요한 상황.

## 2.5 Analysis와 critique

Primary interpretation과 adversarial review는 의도적으로 별도의 artifact입니다.

```text
RESULTS_READY
     ↓
primary analyst
     ↓
03_ANALYSIS.md
     ↓
ANALYZED
     ↓
independent critic
     ↓
04_CRITIQUE.md
     ↓
CRITIQUED
```

동일 provider를 서로 다른 context에서 사용할 수는 있지만, normal Research MCP completion path는 completion 전에 analysis와 critique의 author identity가 서로 다를 것을 요구합니다.

---

# 3. 설치 및 사용 방법

## 3.1 Quick start: local protocol만 사용

Clone하고 설치합니다.

```bash
git clone https://github.com/dlwnsdn0285/research-loop.git
cd research-loop
python -m pip install -e .
```

기존 research repository 안에 Research Loop를 초기화합니다.

```bash
research-loop init /path/to/your-project
```

기존 파일을 보존하면서 protocol, manifest/plan template, agent instruction, provider skill, CI validation이 설치됩니다.

필요하다면 local run을 수동으로 만들 수도 있습니다.

```bash
cd /path/to/your-project
research-loop new "baseline sanity check"
research-loop validate --all
```

이 local mode에서는 MCP가 필요하지 않습니다.

## 3.2 Research MCP 추가

MCP extra를 설치합니다.

```bash
python -m pip install -e '.[mcp]'
```

MCP server가 **자신의 초기화된 research repository**를 바라보도록 설정합니다.

```bash
export RESEARCH_GITHUB_REPO=YOUR_GITHUB_USER/YOUR_RESEARCH_REPO
export GITHUB_TOKEN=YOUR_FINE_GRAINED_GITHUB_TOKEN
export RESEARCH_GITHUB_BRANCH=main
research-mcp
```

Local Streamable HTTP testing:

```bash
research-mcp --transport streamable-http --host 127.0.0.1 --port 8000
```

MCP endpoint는 `/mcp`, liveness endpoint는 `/healthz`입니다.

## 3.3 Remote / self-hosted MCP

Remote ChatGPT/Claude access의 경우 권장 deployment model은 **각 researcher/project가 자신의 MCP deployment와 GitHub credential을 직접 소유하는 방식**입니다.

```text
ChatGPT / Claude
      ↓ HTTPS + OAuth/OIDC
Self-hosted Research MCP
      ↓ repo-scoped GitHub credential
Your research repository
      ↑ git push / pull
Coding Agent
```

다음 파일을 사용합니다.

- [`Dockerfile.research-mcp`](Dockerfile.research-mcp)
- [`cloudbuild.research-mcp.yaml`](cloudbuild.research-mcp.yaml)
- [`research_mcp/.env.remote.example`](research_mcp/.env.remote.example)

일반적인 Google Cloud Run 전체 설정 과정은 [`research_mcp/CLOUD_RUN.md`](research_mcp/CLOUD_RUN.md)에 있습니다.

OAuth를 끄는 것은 local/stdio testing에서만 사용하세요. 인증이 꺼진 HTTP mode를 public internet에 노출하지 마세요.

GitHub credential은 해당 research project에 필요한 최소 repository access만 갖도록 좁게 scope하는 것을 권장합니다. Credential, cloud-provider secret, private project identifier를 commit하지 마세요.

MCP 상세 내용은 [`research_mcp/README.md`](research_mcp/README.md)를 참고하세요.

## 3.4 Normal operating cycle

Repository와 client 연결 이후 권장되는 cycle은 다음과 같습니다.

```text
[Slow Loop]
Human + ChatGPT
    ↓
load durable context
    ↓
discuss uncertainty
    ↓
write plan
    ↓
PLAN_READY

[Fast Loop]
Coding Agent
    ↓
user approval
    ↓
implementation / experiment / validation
    ↓
raw results
    ↓
RESULTS_READY

[Slow Loop]
ChatGPT
    ↓
03_ANALYSIS.md
    ↓
Claude
    ↓
04_CRITIQUE.md
    ↓
Human judgment
    ↓
COMPLETED
    ↓
next cycle
```

---

# 4. 사용 예시

Research Loop의 중요한 점은 researcher가 보통 **MCP API 언어가 아니라 연구 언어로 대화하면 된다**는 것입니다.

## Step 1 — 현재 research state에서 시작

Researcher는 단순히 다음처럼 물을 수 있습니다.

> 현재 research status가 어떻게 돼?

Reasoning client 내부에서는 다음 tool을 사용할 수 있습니다.

```text
get_research_status()
```

하지만 researcher가 tool 이름을 기억할 필요는 없습니다.

## Step 2 — 다음 실험 논의

Researcher가 다음처럼 말합니다.

> 다음 실험을 정해보자. 이전 결과와 critique를 참고하되, 더 엄격한 control에서도 effect가 유지되는지도 확인하고 싶어.

Planner는 durable context를 불러옵니다.

```text
load_planning_context()
        +
current conversation
        ↓
Human + ChatGPT discussion
        ↓
final experiment plan
```

Plan이 durable state가 되기 전에 researcher는 기초적인 질문을 할 수도 있고, assumption을 반박할 수도 있고, constraint를 바꿀 수도 있습니다.

최종적으로 합의가 되면:

```text
create_planned_run(...)
        ↓
PLAN_READY
```

## Step 3 — Coding Agent가 plan 실행

Researcher는 Coding Agent에게 최신 실험을 실행하라고 요청합니다.

Coding Agent는:

```text
pull / sync latest GitHub state
        ↓
read plan
        ↓
explain implementation
        ↓
request approval
        ↓
execute
        ↓
validate
        ↓
record raw/config, raw/metrics, logs, etc.
        ↓
write 02_RESULTS_RAW.md
        ↓
RESULTS_READY
        ↓
commit + push
```

이 시점에는 아직 공식 scientific interpretation이 작성되지 않았습니다.

## Step 4 — chat에서 primary analysis

Conversational interface로 돌아와 researcher가 다음처럼 말합니다.

> 최신 결과를 분석해줘. 중요한 주장은 raw artifact에서 직접 확인하고, 무엇이 달라졌는지 내가 이해할 수 있게 설명해줘.

Reasoning client는 다음을 사용할 수 있습니다.

```text
load_analysis_context()
        ↓
read_run_file(...) when needed
        ↓
conversation with human
        ↓
03_ANALYSIS.md
```

Human은 다음과 같은 질문을 할 수 있습니다.

- 왜 condition A가 B보다 강하지?
- 이게 정말 이전 explanation을 배제하는 건가?
- Evaluation set은 동일한가?
- Baseline artifact일 가능성은 없는가?
- 우리가 안전하게 주장할 수 있는 가장 약한 claim은 무엇인가?

Interpretation을 충분히 이해한 뒤에만 `save_analysis(...)`를 통해 durable state로 저장하는 것이 권장됩니다.

## Step 5 — independent critique

두 번째 reasoning client가 analyzed run을 독립적으로 검토합니다.

유용한 기본값은 다음입니다.

```text
ChatGPT → primary analysis
Claude  → critique
```

Critic은 raw-artifact inventory와 primary analysis를 함께 보고 다음을 challenge합니다.

- hidden assumption;
- confounder;
- comparison fairness;
- overclaiming;
- 누락된 alternative explanation;
- 제안된 다음 실험이 실제로 hypothesis를 구분해주는지 여부.

결과는 `04_CRITIQUE.md`로 저장됩니다.

## Step 6 — human judgment와 completion

Researcher는 analysis와 critique를 비교하고, 남은 disagreement를 토론한 뒤 이 run을 다음 cycle의 durable parent로 사용할 수 있는지 결정합니다.

```text
CRITIQUED
    ↓
Human judgment
    ↓
complete_run()
    ↓
COMPLETED
```

이제 다음 planning cycle은 chat memory가 아니라 이 run을 provenance로 사용할 수 있습니다.

---

# 5. 추가 내용, Warning, Roadmap

## 5.1 Warning: model-role assignment는 heuristic이지 guarantee가 아니다

ChatGPT-planner / Claude-critic 구분은 저자의 실제 사용 경험에서 나온 operational heuristic입니다. 어떤 model이 보편적으로 더 broad하거나, 더 deep하거나, planning이나 critique에 항상 더 우수하다는 benchmark claim이 아닙니다.

자신의 환경에서 충분히 독립적인 reasoning을 만들어내는 provider 조합을 사용하세요.

## 5.2 Warning: Research MCP는 scientific agent가 아니다

Research MCP는 의도적으로 좁은 역할만 가집니다.

다음과 같은 일을 해서는 안 됩니다.

- 다음 research question을 스스로 발명;
- competing scientific explanation 중 하나를 선택;
- experiment plan을 몰래 변경;
- raw measurement를 causal claim으로 변환;
- unexpected result를 보고 새 연구 방향을 시작할지 독자적으로 결정.

이런 decision은 Slow Loop에 속합니다.

## 5.3 Warning: raw result는 raw 상태로 유지되어야 한다

Executor가 `02_RESULTS_RAW.md`를 preferred interpretation에 맞게 더 설득력 있게 다시 작성하도록 두지 마세요.

Raw artifact는 minimally transformed하고 reproducible해야 합니다. Interpretation은 그 이후 단계에 속합니다.

## 5.4 Warning: remote MCP는 실제 security boundary가 필요하다

Auth-off HTTP mode를 public internet에 노출하지 마세요.

권장 deployment 특성은 다음과 같습니다.

- HTTPS;
- OAuth/OIDC protection;
- repository-scoped GitHub credential;
- token commit 대신 secret-manager injection;
- proper multi-tenant isolation을 별도로 구현하지 않는 이상 researcher/project별 MCP deployment.

자세한 내용은 [`research_mcp/CLOUD_RUN.md`](research_mcp/CLOUD_RUN.md)를 참고하세요.

## 5.5 Optional pairing: Research Ponytail

Research Loop는 **research state와 provenance**를 관리합니다. [Research Ponytail](https://github.com/dlwnsdn0285/research-ponytail)은 **research complexity**를 관리합니다.

둘은 서로 complementary하며 강하게 coupling되어 있지는 않습니다.

Research Ponytail은 다음 단계에서 특히 유용합니다.

- planning — root uncertainty를 찾고 가장 작은 decisive experiment를 선택;
- analysis — evidence가 정당화하는 최소 conclusion만 주장;
- critique / next-step selection — 가장 plausible한 failure mode와 결론을 실질적으로 바꿀 수 있는 follow-up에 집중.

Raw-result layer를 변경하는 데 사용해서는 안 됩니다.

유용한 mental model은 다음과 같습니다.

```text
Research Ponytail decides what is worth testing.
Research Loop remembers what was actually tested.
```

## 5.6 Inspiration: LLM Wiki

Research Loop는 Andrej Karpathy의 **LLM Wiki** idea file에서 일부 영감을 받았습니다.

https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f

관련된 영감은 transient conversation에서 durable state를 꺼내 filesystem artifact로 옮기고, Agent가 이를 장기간 관리할 수 있도록 하되 source material과 LLM-maintained derived material을 구분한다는 더 넓은 패턴입니다.

Research Loop는 이 아이디어를 computational experiment lifecycle에 적용하여 explicit plan, human approval, raw-result isolation, analysis, critique, state, provenance를 추가합니다.

LLM Wiki gist의 text/code를 이 repository에 포함하지 않았습니다. Attribution 및 licensing 관련 내용은 [`NOTICE.md`](NOTICE.md)를 참고하세요.

## 5.7 현재 limitation: Coding Agent repository synchronization

v0.2의 normal executor path는 Coding Agent가 local checkout에서 작업하고, 실행 전에 canonical GitHub repository를 동기화한다고 가정합니다.

```text
GitHub canonical repo
        ↓ git pull / fetch
local research checkout
        ↓
Coding Agent execution
```

이 방식은 단순하고 명시적이지만 friction이 있습니다.

- local checkout이 stale해질 수 있음;
- Coding Agent가 매번 새로운 run 전에 sync해야 함;
- merge conflict가 Fast Loop를 중단시킬 수 있음;
- local working repository와 configured GitHub research repository가 항상 동일한 source tree를 가리키지 않을 수 있음.

따라서 현재 agent instruction은 sync check를 요구하고 예상치 못한 divergence가 있으면 escalation하도록 합니다.

## 5.8 Roadmap: Coding Agent의 direct GitHub source access

향후 버전에서는 반복적인 manual/local synchronization 의존도를 줄이는 것이 목표입니다.

의도한 방향은 다음과 같습니다.

```text
Current v0.2

GitHub
  ↓ pull
Local checkout
  ↓
Coding Agent


Possible future version

GitHub canonical source
  ↓ direct source / state access
Coding Agent
  ↓ execution workspace
results
  ↓
GitHub
```

목표는 Coding Agent가 run을 시작할 때 현재 local checkout이 이미 정확하고 최신 repository라고 가정하는 대신, canonical source를 GitHub에서 직접 resolve하도록 하는 것입니다.

다만 writable working tree, uncommitted local change, reproducibility, authentication에 대한 추가 설계가 필요합니다.

## 5.9 Open compatibility question: Claude Code와 repository identity

또 다른 unresolved issue는 Coding Agent의 current working directory와 Research MCP에 설정된 GitHub repository가 서로 다를 때의 repository identity입니다.

예를 들어:

```text
Claude Code current workspace
        = local/project-A

Research MCP durable repo
        = github.com/user/project-B
```

명시적인 protocol이 필요한 질문은 다음과 같습니다.

- Source code의 authoritative repository는 어느 쪽인가?
- Local `origin`이 configured durable repository와 다르면 Coding Agent가 execution을 거부해야 하는가?
- Research-state repository와 experiment-code repository가 의도적으로 달라도 되는가?
- 서로 다르다면 commit SHA와 provenance는 두 repository를 어떻게 연결해야 하는가?
- MCP가 execution 전에 canonical repository identity를 Coding Agent에 제공해야 하는가?

이 부분이 formalize되기 전까지 가장 안전한 v0.2 동작은 repository mismatch 또는 예상하지 못한 divergence를 추측으로 해결하지 않고 escalation condition으로 처리하는 것입니다.

## 5.10 Status

**v0.2 prototype.** Local Git-backed protocol과 self-hostable Research MCP가 구현되어 있습니다. 반복적인 real-world research cycle에서 friction이 발견되면서 interface가 변경될 수 있습니다.

Stable `v1.0`은 여러 번의 완전한 planning → execution → analysis → critique cycle을 실제로 통과한 이후가 적절합니다.

## 5.11 License

Research Loop는 MIT License로 배포됩니다. [`LICENSE`](LICENSE)를 참고하세요.

Third-party inspiration 및 attribution은 [`NOTICE.md`](NOTICE.md)에 설명되어 있습니다.
