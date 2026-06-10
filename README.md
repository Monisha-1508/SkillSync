<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:001E3C,50:0070AD,100:17ABDA&height=200&section=header&text=SkillSync%20AI&fontSize=60&fontColor=ffffff&fontAlignY=38&desc=AI-Powered%20Placement%20Preparation%20Platform&descAlignY=58&descSize=18&animation=fadeIn" width="100%"/>

<br/>

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Visit%20Now-17ABDA?style=for-the-badge&labelColor=001E3C)](https://skillsync-ai.placeholder.io)
[![Documentation](https://img.shields.io/badge/Docs-Read%20Here-0070AD?style=for-the-badge&labelColor=001E3C)](#table-of-contents)
[![Report Bug](https://img.shields.io/badge/Bug-Report%20Issue-FF6B6B?style=for-the-badge&labelColor=001E3C)](https://github.com/Monisha-1508/SKILLSYNC_AI/issues)

<br/>

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-15-black?style=flat-square&logo=next.js&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-Orchestration-1DB954?style=flat-square&logo=langchain&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-412991?style=flat-square&logo=openai&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?style=flat-square&logo=sqlite&logoColor=white)
![Tailwind](https://img.shields.io/badge/Tailwind-CSS-06B6D4?style=flat-square&logo=tailwindcss&logoColor=white)
![OpenTelemetry](https://img.shields.io/badge/OpenTelemetry-Tracing-F5A800?style=flat-square&logo=opentelemetry&logoColor=black)

<br/>

![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Build](https://img.shields.io/badge/Build-Passing-brightgreen?style=flat-square&logo=github-actions)
![Tests](https://img.shields.io/badge/Tests-5%2F5%20Passing-brightgreen?style=flat-square&logo=pytest)
![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-0070AD?style=flat-square)
![Hackathon](https://img.shields.io/badge/Capgemini-Hackathon%202026-FF6B35?style=flat-square)

</div>

---

## Table of Contents

<details open>
<summary><strong>Expand</strong></summary>

- [About](#about)
- [Features](#features)
- [System Architecture](#system-architecture)
- [The Six Agents](#the-six-agents)
- [LangGraph Pipeline](#langgraph-pipeline)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Dashboard Panels](#dashboard-panels)
- [Running Tests](#running-tests)
- [Project Structure](#project-structure)
- [Proctoring System](#proctoring-system)
- [Observability](#observability)
- [Contributing](#contributing)

</details>

---

## About

SkillSync AI is a multi-agent placement prep platform built for the Capgemini Hackathon 2026 (AI-Assisted Learning track). Fill in a short intake form - target role, current skill levels, weekly hours, deadline - and six specialised agents run in sequence to build a personalised week-by-week study plan.

Every agent decision is logged and streamed live to the screen during onboarding. You can watch the gap analysis run, see the roadmap being built, and read the validator's sign-off before you start studying. Nothing happens in a black box.

Three things it does well:

- **Skill gap analysis** - maps self-rated skills against what the target role needs, using a 41-node graph with an India placement overlay
- **Three-variant roadmap** - generates Safe, Target, and Stretch plans sized to real available hours, not a generic 40-hour week
- **Proctored checkpoints and mock interviews** - weekly MCQ tests and role-specific interview rounds, both with anti-cheat measures baked in

A demo account seeds automatically so you can explore the full dashboard without going through onboarding.

---

## Features

| Feature | What it does |
|:---|:---|
| Skill Gap Map | Radar chart across 41 skills - covered, developing, gap, unknown buckets |
| Three-Variant Roadmap | Safe, Target, Stretch - feasibility score per variant based on actual hours |
| Curated Resources | Trust-scored corpus locked by week, respects free vs paid preference |
| FSRS Revision Deck | Spaced-repetition flashcards using FSRS-4.5 - cards surface when due |
| Proctored Checkpoints | MCQ tests per week, copy-paste and tab-switch detection built in |
| Mock Interviews | Role-specific question banks per company drive, rubric grading |
| Dynamic Reflow | Missed weeks merge forward automatically so the plan stays usable |
| Learning Recovery | Fail a checkpoint twice and a recovery micro-evaluation kicks in |
| Gamification | Points, levels, and badges from actual logged progress |
| Deadline Alerts | Banner fires when logged pace trails what the deadline needs |
| Audit Trail | Every agent step logged with confidence score, streamed live |
| Validation Sign-off | Separate validator agent runs 5 checks before the plan reaches you |

---

## System Architecture

```mermaid
graph TB
    subgraph CLIENT["Browser Client - Next.js 15"]
        LP[Landing Page]
        OB[Onboarding Flow]
        DB[Dashboard - 9 Panels, 9 Tabs]
        SSE[SSE Stream - Live Agent Trace]
    end

    subgraph GATEWAY["FastAPI Backend - Python 3.11"]
        AUTH[Auth Router]
        PROF[Profiles Router]
        DASH[Dashboard Router]
        RM[Roadmap Router]
        WT[Weekly Test Router]
        REV[Revision Router]
        INT[Interview Router]
        REC[Recovery Router]
        EXP[Explain Router]
    end

    subgraph PIPELINE["LangGraph Agent Pipeline"]
        SUP{Supervisor}
        AG1[Profiling]
        AG2[Roadmap Architect]
        AG3[Resource Curator]
        AG4[Coach]
        AG5[Validator]
        AG6[Interviewer]
    end

    subgraph DATA["Data Layer"]
        DB2[(SQLite / Postgres)]
        GRAPH[Skill Graph - 41 nodes]
        RBANK[Resource Bank]
        DBANK[Drive Banks - 4 companies]
        OTEL[OpenTelemetry]
    end

    CLIENT -->|REST + SSE| GATEWAY
    GATEWAY -->|Invoke| PIPELINE
    PIPELINE -->|Read/Write| DATA
    GATEWAY -->|Read/Write| DATA

    style CLIENT fill:#17ABDA,color:#001E3C,stroke:#0070AD
    style GATEWAY fill:#0070AD,color:#ffffff,stroke:#001E3C
    style PIPELINE fill:#001E3C,color:#ffffff,stroke:#17ABDA
    style DATA fill:#F0F4F8,color:#001E3C,stroke:#0070AD
```

---

## The Six Agents

```mermaid
graph LR
    A["Profiling\n─────────\nMaps self-ratings onto\n41-node skill graph\nInfers gaps via proximity"]
    B["Roadmap Architect\n─────────\nBuilds Safe, Target,\nStretch plans sized\nto available hours"]
    C["Resource Curator\n─────────\nTrust-scores resources\non 5 factors, enforces\n0.55 trust floor"]
    D["Coach\n─────────\nWatches engagement\nsignals, proposes\nre-plans when pace slips"]
    E["Validator\n─────────\n5 independent checks\nbefore the plan\nreaches the learner"]
    F["Interviewer\n─────────\nCompany drive Q banks\nrubric grading\nanti-cheat proctoring"]

    A --> B --> C --> D --> E
    D -.->|replan loop| B
    F -.->|independent path| E

    style A fill:#17ABDA,color:#001E3C,stroke:#0070AD,stroke-width:2px
    style B fill:#0070AD,color:#ffffff,stroke:#001E3C,stroke-width:2px
    style C fill:#001E3C,color:#ffffff,stroke:#17ABDA,stroke-width:2px
    style D fill:#38D9A9,color:#001E3C,stroke:#0070AD,stroke-width:2px
    style E fill:#FF6B6B,color:#ffffff,stroke:#001E3C,stroke-width:2px
    style F fill:#CC5DE8,color:#ffffff,stroke:#001E3C,stroke-width:2px
```

<details>
<summary><strong>Profiling Agent</strong></summary>

Takes learner self-ratings across 41 skill nodes grouped into 6 families and builds a gap map. Unrated nodes are inferred from graph proximity using `skill_chains.py`. Output is covered / developing / gap / unknown buckets plus a confidence score that drives the responsible AI disclosure shown on the dashboard.

</details>

<details>
<summary><strong>Roadmap Architect</strong></summary>

Reads the gap map and target role, then drafts three variants using the feasibility engine in `feasibility.py`. Each variant gets a score calculated from hours available vs hours needed. Prerequisites are always sequenced before dependents. Blackout weeks are marked. Supports re-planning mid-run when the Coach flags a pace issue.

</details>

<details>
<summary><strong>Resource Curator</strong></summary>

Scores resources from `resource_bank.py` against a 5-factor trust formula. Anything below 0.55 is excluded. Resources lock to the week they become available based on roadmap state. Free vs paid preference set at intake is respected throughout.

</details>

<details>
<summary><strong>Coach</strong></summary>

Reads completion rate, quiz scores, and streak data. Proposes a re-plan when pace trails the runway by a configurable threshold. The learner approves or rejects before anything changes. Also drives the reflow engine when a week is logged as missed.

</details>

<details>
<summary><strong>Validator</strong></summary>

Runs independently after the pipeline. Five checks: resource trust floor, prerequisite ordering, feasibility margin, skill coverage, plan completeness. Produces overall pass / flagged status logged with a timestamp and surfaced in its own dashboard tab.

</details>

<details>
<summary><strong>Interviewer</strong></summary>

Uses `drive_banks.py` for company-specific question banks across four drives (Infosys, TCS, Wipro, Capgemini). Supports MCQ and open-ended questions. Grades on a per-dimension rubric and produces section breakdowns and drive benchmarks. The same proctoring layer as weekly checkpoints applies here.

</details>

---

## LangGraph Pipeline

```mermaid
sequenceDiagram
    participant U as Learner
    participant FE as Next.js
    participant BE as FastAPI
    participant SUP as LangGraph Supervisor
    participant DB as Database

    U->>FE: Submit intake form
    FE->>BE: POST /api/profiles
    BE->>SUP: Invoke pipeline
    SUP->>SUP: profile_gaps node
    SUP-->>FE: SSE: profiling_complete
    SUP->>SUP: build_roadmap node
    SUP-->>FE: SSE: roadmap_ready
    SUP->>SUP: curate_resources node
    SUP-->>FE: SSE: resources_locked
    SUP->>SUP: draft_revision_deck node
    SUP-->>FE: SSE: deck_built
    SUP->>SUP: validate_plan node
    SUP-->>FE: SSE: validation_done
    SUP->>DB: Persist outputs
    BE-->>FE: Pipeline complete
    FE->>U: Dashboard ready
```

---

## Tech Stack

### Backend

| Layer | Technology | Notes |
|:---|:---|:---|
| Language | Python 3.11+ | |
| Framework | FastAPI 0.115 | Async, SSE streaming |
| Orchestration | LangGraph 0.2 | 5-node supervisor graph |
| LLM | OpenAI GPT-4o-mini / Azure OpenAI | Swappable via `llm.py` |
| ORM | SQLAlchemy 2.0 async | |
| Database | SQLite (dev) / PostgreSQL (prod) | |
| Auth | PyJWT + BCrypt | Bearer token |
| Spaced Rep | FSRS-4.5 | `fsrs_engine.py` |
| Feasibility | Custom scorer | `feasibility.py` |
| Narration | Template engine | `narration.py` |
| Observability | OpenTelemetry | `tracing.py` |

### Frontend

| Layer | Technology | Notes |
|:---|:---|:---|
| Framework | Next.js 15 App Router | |
| Styling | Tailwind CSS 3 | Capgemini brand tokens |
| Charts | Recharts | Radar, bar, progress |
| Icons | Lucide React | |
| Streaming | EventSource / SSE | Live onboarding trace |

---

## Getting Started

### Requirements

- Python 3.11+
- Node.js 18+
- npm 9+
- OpenAI or Azure OpenAI key (optional - `simulated` mode works offline)

### 1. Clone

```bash
git clone https://github.com/Monisha-1508/SKILLSYNC_AI.git
cd SKILLSYNC_AI
```

### 2. Backend

```bash
cd backend

python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Frontend

```bash
cd frontend
npm install
```

### 4. Environment

Copy the example file and fill in values:

```bash
cp backend/.env.example backend/.env
```

```env
# "simulated" works offline with no API key
LLM_PROVIDER=simulated

# OpenAI
OPENAI_API_KEY=sk-...

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4o

# Database - defaults to SQLite
DATABASE_URL=sqlite+aiosqlite:///./data/skillsync.db

CORS_ORIGINS=http://localhost:3000
```

### 5. Run

**Terminal 1 - backend:**

```bash
cd backend
uvicorn main:app --reload --port 8000
```

**Terminal 2 - frontend:**

```bash
cd frontend
npm run dev
```

### 6. Open

| URL | What it is |
|:---|:---|
| `http://localhost:3000` | Frontend |
| `http://localhost:8000/docs` | FastAPI Swagger UI |
| `http://localhost:8000/api/health` | Health check |

### Demo account

Seeded automatically on first backend start:

```
Email    :  demo@skillsync.ai
Password :  skillsync-demo
```

Five pre-built personas (Aarav, Priya, Rohan, Sneha, Vikram) are available on the onboarding screen to skip the intake form.

---

## Configuration

<details>
<summary><strong>LLM provider options</strong></summary>

| Value | Description |
|:---|:---|
| `simulated` | No API key needed. Deterministic mock responses. |
| `openai` | OpenAI API. Needs `OPENAI_API_KEY`. |
| `azure_openai` | Azure OpenAI. Needs endpoint, key, deployment. |

</details>

<details>
<summary><strong>Database</strong></summary>

```env
# SQLite - zero config
DATABASE_URL=sqlite+aiosqlite:///./data/skillsync.db

# PostgreSQL
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/skillsync
```

</details>

---

## API Reference

<details>
<summary><strong>Auth</strong></summary>

| Method | Endpoint | Description |
|:---|:---|:---|
| POST | `/api/auth/register` | Create account |
| POST | `/api/auth/login` | Log in, get JWT |
| GET | `/api/auth/me` | Current user |

</details>

<details>
<summary><strong>Profiles and onboarding</strong></summary>

| Method | Endpoint | Description |
|:---|:---|:---|
| GET | `/api/personas` | List demo personas |
| POST | `/api/profiles` | Create from intake form |
| POST | `/api/profiles/from-persona/{key}` | Instant profile from persona |
| GET | `/api/profiles/mine` | All plans for current user |
| GET | `/api/profiles/{id}/onboarding-stream` | SSE live agent trace |

</details>

<details>
<summary><strong>Dashboard and roadmap</strong></summary>

| Method | Endpoint | Description |
|:---|:---|:---|
| GET | `/api/dashboard/{profile_id}` | Full aggregated dashboard |
| POST | `/api/roadmap/{id}/select` | Switch variant |
| POST | `/api/roadmap/{id}/progress` | Log week |
| POST | `/api/roadmap/{id}/replan/propose` | Request re-plan |
| POST | `/api/roadmap/{id}/replan/decide` | Approve or reject |
| POST | `/api/roadmap/{id}/reflow/{week}` | Merge missed week forward |

</details>

<details>
<summary><strong>Weekly checkpoints</strong></summary>

| Method | Endpoint | Description |
|:---|:---|:---|
| GET | `/api/weekly-test/{id}/board` | Board state |
| POST | `/api/weekly-test/{id}/start` | Start a sitting |
| POST | `/api/weekly-test/{id}/answer` | Submit answer |

</details>

<details>
<summary><strong>Revision, interview, recovery</strong></summary>

| Method | Endpoint | Description |
|:---|:---|:---|
| GET | `/api/revision/{id}/deck` | Due flashcards |
| POST | `/api/revision/{id}/review` | Grade card (FSRS) |
| POST | `/api/interview/{id}/start` | Start mock round |
| POST | `/api/interview/{id}/answer` | Submit answer |
| GET | `/api/recovery/{id}/{week}/status` | Recovery gate |
| POST | `/api/recovery/{id}/{week}/start` | Start micro-eval |
| POST | `/api/recovery/{id}/answer` | Submit recovery answer |

</details>

---

## Dashboard Panels

| Tab | What you see |
|:---|:---|
| Overview | Summary cards, gamification bar, gap snapshot, validator sign-off |
| Gap Map | Radar chart across 6 skill families, bucket breakdown |
| Roadmap | Week-by-week milestones, reflow indicators, feasibility score |
| Progress | Log each week complete / partial / missed, trigger reflow |
| Resources | Trust-scored cards per skill, locked until week unlocked |
| Revision | FSRS flashcard deck - flip and grade Again / Hard / Good / Easy |
| Mock Interview | Pick company drive and round, answer under timer, post-round report |
| Checkpoint | Proctored weekly MCQ, learning recovery panel if retake gate fires |
| Validation | Full validator report with per-check status and timestamps |

---

## Running Tests

```bash
cd backend

# Windows
$env:PYTHONPATH = "C:\path\to\SKILLSYNC_AI"
.venv\Scripts\python -m pytest tests/ -v

# macOS / Linux
export PYTHONPATH=/path/to/SKILLSYNC_AI
.venv/bin/python -m pytest tests/ -v
```

Expected output:

```
tests/test_profiling_e2e.py::test_profiling_persona_cold_run[aarav]   PASSED
tests/test_profiling_e2e.py::test_profiling_persona_cold_run[priya]   PASSED
tests/test_profiling_e2e.py::test_profiling_persona_cold_run[rohan]   PASSED
tests/test_profiling_e2e.py::test_profiling_persona_cold_run[sneha]   PASSED
tests/test_profiling_e2e.py::test_profiling_persona_cold_run[vikram]  PASSED

5 passed in 3.23s
```

---

## Project Structure

```
SKILLSYNC_AI/
|
+-- backend/
|   +-- agents/
|   |   +-- supervisor.py          LangGraph 5-node pipeline
|   |   +-- profiling.py           Skill gap analysis
|   |   +-- roadmap_architect.py   3-variant roadmap generation
|   |   +-- resource_curator.py    Trust-scored resource selection
|   |   +-- coach.py               Engagement + re-plan logic
|   |   +-- validator.py           5-check validation
|   |   +-- interviewer.py         Mock interview generation
|   |   +-- weekly_test.py         MCQ generation + grading
|   |   +-- learning_recovery.py   Diagnosis + micro-evaluation
|   |   +-- reflow.py              Deterministic week reflow
|   |   +-- project_advisor.py     Post-completion project suggestions
|   |
|   +-- data/
|   |   +-- skill_graph.json       41-node skill graph
|   |   +-- skill_chains.py        Prerequisite chain definitions
|   |   +-- resource_bank.py       Trust-scored resource corpus
|   |   +-- drive_banks.py         Company-specific interview Q banks
|   |   +-- company_profiles.json  Drive metadata (Infosys, TCS, Wipro, Capgemini)
|   |   +-- project_bank.py        Role-tagged project suggestions
|   |   +-- demo_personas.json     5 pre-built learner personas
|   |   +-- golden_eval.json       Golden evaluation dataset
|   |
|   +-- models/
|   |   +-- database.py            SQLAlchemy async models
|   |   +-- schemas.py             Pydantic schemas
|   |   +-- state.py               LangGraph state TypedDict
|   |
|   +-- routers/
|   |   +-- auth.py                JWT auth
|   |   +-- profiles.py            Intake + SSE stream
|   |   +-- dashboard.py           Aggregated dashboard
|   |   +-- roadmap.py             Progress, replan, reflow
|   |   +-- revision.py            FSRS deck
|   |   +-- weekly_test.py         Proctored checkpoint
|   |   +-- interview.py           Mock interview rounds
|   |   +-- recovery.py            Learning recovery
|   |   +-- explain.py             Skill/resource/replan explainer
|   |   +-- deps.py                Shared FastAPI dependencies
|   |
|   +-- utils/
|   |   +-- auth.py                Password hashing + JWT
|   |   +-- feasibility.py         Roadmap feasibility scorer
|   |   +-- fsrs_engine.py         FSRS-4.5 spaced repetition
|   |   +-- gamification.py        Points, levels, badges
|   |   +-- llm.py                 LLM abstraction layer
|   |   +-- narration.py           Plan narration templates
|   |   +-- persistence.py         DB read/write helpers
|   |   +-- responsible_ai.py      Confidence + disclosure
|   |   +-- seed.py                DB seeding + demo account
|   |   +-- skill_graph.py         Graph traversal helpers
|   |   +-- tracing.py             OpenTelemetry setup
|   |
|   +-- tests/
|   |   +-- test_profiling_e2e.py
|   |
|   +-- config.py                  Pydantic settings, env-driven
|   +-- main.py                    App entry, router wiring, CORS
|
+-- frontend/
|   +-- src/
|   |   +-- app/
|   |   |   +-- page.js            Landing page
|   |   |   +-- layout.js          Root layout
|   |   |   +-- login/page.js      Login + register
|   |   |   +-- onboarding/page.js Intake form + trace view
|   |   |   +-- dashboard/page.js  Main dashboard, 9 tabs
|   |   |   +-- plans/page.js      Account hub, all plans
|   |   |
|   |   +-- components/
|   |   |   +-- panels/            11 dashboard panel components
|   |   |   +-- OnboardingTrace.js SSE trace display
|   |   |   +-- GamificationReward.js Points + badges overlay
|   |   |   +-- Celebration.js     Confetti + balloon animations
|   |   |   +-- AlertBanner.js     Deadline alert strip
|   |   |   +-- ui.js              Shared UI primitives
|   |   |
|   |   +-- lib/
|   |   |   +-- api.js             Fetch wrapper + auth token
|   |   |   +-- AuthContext.js     React auth state
|   |   |   +-- cx.js              Class name utility
|   |   |
|   |   +-- styles/
|   |       +-- globals.css        Tailwind base + custom animations
|   |
|   +-- tailwind.config.js         Brand color tokens
|   +-- next.config.js             API proxy to port 8000
|   +-- package.json
|
+-- .gitignore
+-- README.md
```

---

## Proctoring System

Both weekly checkpoints and mock interview rounds use the same anti-cheat layer.

```mermaid
graph LR
    subgraph TRACK["What gets tracked"]
        CP[Copy-paste attempts]
        TS[Tab switches - max 3]
        FS[Fullscreen exits]
        TM[Per-question timer]
    end

    CP -->|any attempt| BLOCK[Celebration suppressed]
    TS -->|more than 3| BLOCK
    FS -->|any exit| BLOCK
    TM -->|hits zero| AUTO[Auto-submit]

    PASS[All clear] --> CELEB[Full celebration overlay]

    style TRACK fill:#001E3C,color:#ffffff,stroke:#17ABDA
    style CELEB fill:#38D9A9,color:#001E3C,stroke:#0070AD
    style BLOCK fill:#FF6B6B,color:#ffffff,stroke:#001E3C
```

---

## Observability

```mermaid
graph TD
    AGT[Agent Step] -->|traced_step ctx manager| SPAN[OpenTelemetry Span]
    SPAN --> ATTR[agent_name, action, confidence, output_summary]
    ATTR --> AUDIT[AuditLog table]
    AUDIT --> DASH[Dashboard Audit Trail panel]
    SPAN --> CONSOLE[Console exporter - dev mode]

    style AGT fill:#0070AD,color:#ffffff
    style SPAN fill:#F5A800,color:#001E3C
    style AUDIT fill:#001E3C,color:#ffffff
    style DASH fill:#17ABDA,color:#001E3C
```

Every agent step wraps in a `traced_step` context manager that emits an OpenTelemetry span. The span carries the agent name, action, confidence score, and output summary. These persist to the `AuditLog` table and surface in the dashboard's Audit Trail panel.

---

## Contributing

1. Fork the repo
2. Create a branch: `git checkout -b feature/your-feature`
3. Commit: `git commit -m 'Add your feature'`
4. Push: `git push origin feature/your-feature`
5. Open a pull request

---

<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:17ABDA,50:0070AD,100:001E3C&height=120&section=footer&animation=fadeIn" width="100%"/>

<br/>

[![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-black?style=flat-square&logo=next.js&logoColor=white)](https://nextjs.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-1DB954?style=flat-square)](https://github.com/langchain-ai/langgraph)

<br/>

Capgemini Hackathon 2026 - AI-Assisted Learning Track

</div>
