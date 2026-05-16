# Attention-Aware Study Assistant — Requirement Specification Document

## 1. Project Overview

### 1.1 Problem Statement
Traditional e-learning platforms deliver static content irrespective of the learner's cognitive state. Research in **Sweller's Cognitive Load Theory (CLT)** demonstrates that working memory is limited in both capacity and duration. When total cognitive load — comprising intrinsic load (material difficulty), extraneous load (poor design), and germane load (actual learning effort) — exceeds capacity, **attention fatigue** sets in, causing reduced retention, increased errors, and disengagement.

### 1.2 Proposed Solution
The **Attention-Aware Study Assistant** is an agentic, cloud-native NLP system that continuously monitors a learner's cognitive state through non-intrusive behavioural signals and adapts teaching content in real time. The system implements a **ReAct-style (Reason + Act) agentic loop** through a central orchestrator, switching between four adaptive teaching modes based on measured fatigue.

### 1.3 Target Users
- University students studying complex technical subjects
- Self-learners using online resources
- Educators wanting to understand student engagement patterns

---

## 2. Domain Research Summary

### 2.1 Cognitive Load Theory (Sweller, 1988)
| Load Type | Description | System Response |
|-----------|-------------|-----------------|
| **Intrinsic** | Inherent difficulty of material | Adjust content difficulty dynamically |
| **Extraneous** | Unnecessary cognitive burden from poor design | Simplify presentation, reduce noise |
| **Germane** | Effort spent building mental schemas | Maximise through scaffolding & analogies |

### 2.2 Attention-Fatigue Indicators (Keystroke Dynamics Research)
Research confirms that keystroke dynamics serve as reliable, non-intrusive biomarkers for cognitive state:

| Signal | Fatigue Indicator | Citation |
|--------|-------------------|----------|
| **Typing Speed** | Decreases with fatigue | BiAffect (2023), IJCRT (2024) |
| **Speed Variance** | Increases with attention drift | ResearchGate (2023) |
| **Inter-Key Latency** | Longer/more erratic with cognitive slowing | Wikipedia, TU/e studies |
| **Error Rate (backspaces)** | Increases under cognitive load | AIJFR (2024) |
| **Pause Patterns** | Irregular pauses signal mental exhaustion | AIUB (2023) |
| **Response Delay** | Increased time-to-answer correlates with fatigue | Multiple CLT studies |
| **Quiz Performance Trend** | Dropping accuracy signals overload | CLT + adaptive learning literature |

### 2.3 Adaptive Teaching Modes (Evidence-Based)
The system implements four modes grounded in pedagogical research:

1. **Detailed Mode** (FRESH state) — Full explanations with examples. Leverages germane load when working memory is available.
2. **Concise Mode** (MODERATE fatigue) — Bullet-pointed key facts. Reduces extraneous load.
3. **Analogy Mode** (TIRED state) — Metaphors and relatable stories. Activates prior schema to reduce intrinsic load.
4. **Quiz Mode** (EXHAUSTED / interval trigger) — Active recall with instant feedback. Prevents passive absorption and tests retention.

---

## 3. User Stories

### 3.1 Learner Stories
| ID | Story | Priority |
|----|-------|----------|
| US-01 | As a learner, I want to enter a study topic and receive adaptive explanations so that content matches my current energy level. | **Must Have** |
| US-02 | As a learner, I want the system to automatically detect my fatigue from my typing patterns so that I don't have to self-report. | **Must Have** |
| US-03 | As a learner, I want to take quizzes that adapt in difficulty based on my mastery so that I'm always challenged but not overwhelmed. | **Must Have** |
| US-04 | As a learner, I want to see a real-time fatigue gauge so that I'm aware of my own cognitive state. | **Should Have** |
| US-05 | As a learner, I want to manually override the teaching mode if I prefer a different style. | **Should Have** |
| US-06 | As a learner, I want to view a session summary at the end so that I can review what I learned. | **Should Have** |
| US-07 | As a learner, I want my progress to be saved across sessions so that the system remembers my mastery level. | **Could Have** |
| US-08 | As a learner, I want to export my session data as JSON for offline review. | **Could Have** |

### 3.2 System / Developer Stories
| ID | Story | Priority |
|----|-------|----------|
| US-09 | As a developer, I want each service to run independently so that I can test and deploy them separately. | **Must Have** |
| US-10 | As a developer, I want all inter-service communication to flow through the Orchestrator so that the architecture remains clean. | **Must Have** |
| US-11 | As a developer, I want the database layer to support both SQLite (dev) and PostgreSQL (prod) so that cloud deployment is seamless. | **Could Have** |

---

## 4. System Constraints

### 4.1 Technical Constraints
- **Language**: Python 3.10+
- **LLM Provider**: Anthropic Claude API (claude-sonnet-4-20250514) — used for content generation, quiz evaluation, and session summaries
- **Backend Framework**: FastAPI with Uvicorn ASGI server
- **Frontend**: Streamlit (Python-based, rapid prototyping)
- **Database**: SQLite (development) / Supabase PostgreSQL (production)
- **Inter-service Communication**: HTTP/JSON via httpx AsyncClient
- **Prompt Templating**: Jinja2

### 4.2 Performance Constraints
- Each /interact call must complete within **5 seconds** (including LLM latency)
- Concurrent calls to Attention Monitor + Learner Profiler via `asyncio.gather()` to reduce latency
- Streaming responses (SSE) for content generation to improve perceived speed

### 4.3 Security Constraints
- Anthropic API key stored in environment variable (`ANTHROPIC_API_KEY`), never committed
- `.env.example` provided without real keys
- Session IDs used as lightweight user identifiers (no auth system in hackathon scope)

### 4.4 Deployment Constraints
- Frontend: Streamlit Cloud (free tier)
- Backend: Render.com (free tier, one Web Service per microservice)
- Environment variables for all secrets and service URLs

---

## 5. NLP Pipeline Architecture

### 5.1 Agentic ReAct Loop
Every user interaction triggers a four-step cognitive cycle:

```
┌─────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR AGENT                     │
│                                                          │
│  1. OBSERVE  → Collect: user message, keypress           │
│                telemetry bundle, session ID               │
│                                                          │
│  2. REASON   → Call Attention Monitor (fatigue score)     │
│                + Learner Profiler (mastery, history)      │
│                concurrently. Decide mode.                 │
│                                                          │
│  3. ACT      → Dispatch to Content Adaptation Agent      │
│                OR Quiz Engine Agent. Stream response.     │
│                                                          │
│  4. REFLECT  → Update Learner Profile with outcome.      │
│                Log to Data Persistence Service.           │
│                Adjust next-call parameters.               │
└─────────────────────────────────────────────────────────┘
```

### 5.2 Fatigue Classification Pipeline
```
Raw Signals              Weighted Heuristic           Classification
─────────────           ──────────────────          ────────────────
Keypress intervals ──┐
                     ├──→ Weighted score (0-1) ──→ FRESH (0-0.25)
Response delay ──────┤                              MODERATE (0.25-0.50)
                     │                              TIRED (0.50-0.75)
Quiz score trend ────┘                              EXHAUSTED (0.75-1.0)
```

### 5.3 Content Adaptation Pipeline
```
Inputs                       LLM Call                      Output
──────                      ────────                      ──────
Topic + Fatigue Label ──┐
                        ├──→ Jinja2 Template ──→ Claude API ──→ Adaptive Markdown
Learner Profile ────────┤    (mode-specific)     (streaming)    + metadata
                        │
Difficulty Level ───────┘
```

### 5.4 Mode Selection Logic
```python
def select_mode(fatigue_label: str, profile: LearnerProfile) -> str:
    if fatigue_label == "EXHAUSTED":
        return "quiz"
    elif fatigue_label == "TIRED":
        return "analogy"
    elif fatigue_label == "MODERATE":
        return "concise"
    else:  # FRESH
        return "detailed"
```

---

## 6. Microservices Architecture

### 6.1 Service Catalogue
| ID | Service | Port | Responsibility |
|----|---------|------|---------------|
| SVC-01 | Attention Monitor Agent | 8001 | Passive fatigue classification from behavioural signals |
| SVC-02 | Learner Profiler Agent | 8002 | Session context, mastery tracking, profile persistence |
| SVC-03 | Content Adaptation Agent | 8003 | Dynamic AI content generation in 4 modes |
| SVC-04 | Quiz Engine Agent | 8004 | Question generation, answer evaluation, scoring |
| SVC-05 | Orchestrator Agent | 8000 | Central coordinator — ReAct agentic loop |
| SVC-06 | Data Persistence Service | 8005 | Centralised storage & retrieval (SQLite/PostgreSQL) |
| SVC-07 | Streamlit Frontend | 8501 | User-facing interactive interface |

### 6.2 Communication Flow
```
Frontend (8501) ──POST /interact──→ Orchestrator (8000)
                                        │
                    ┌───────────────────┼───────────────────┐
                    ▼                   ▼                   ▼
            Attention Monitor    Learner Profiler    Data Persistence
               (8001)              (8002)              (8005)
                    │                   │
                    └───────┬───────────┘
                            ▼
                    Mode Decision Engine
                            │
                    ┌───────┴───────┐
                    ▼               ▼
            Content Adapter   Quiz Engine
               (8003)          (8004)
                    │               │
                    └───────┬───────┘
                            ▼
                    Claude API (External)
```

### 6.3 Hub-and-Spoke Pattern
All inter-agent communication flows through the Orchestrator. No agent calls another agent directly. This ensures:
- Clear separation of concerns
- Easy debugging (single point of observation)
- Independent deployability of each service

---

## 7. Data Models (Key Schemas)

### 7.1 FatigueState
```json
{
  "score": 0.62,
  "label": "TIRED",
  "confidence": 0.85,
  "signals": {
    "keypress_variance": 0.7,
    "response_delay_norm": 0.5,
    "quiz_trend": -0.3
  }
}
```

### 7.2 LearnerProfile
```json
{
  "session_id": "abc-123",
  "topic": "machine_learning",
  "mastery_score": 0.45,
  "preferred_mode": "analogy",
  "avg_fatigue": 0.55,
  "difficulty_level": 3,
  "last_seen": "2026-05-16T10:30:00Z"
}
```

### 7.3 InteractionLog
```json
{
  "session_id": "abc-123",
  "timestamp": "2026-05-16T10:31:00Z",
  "mode_used": "analogy",
  "fatigue_score": 0.62,
  "content_snippet": "Think of neural networks like...",
  "user_message": "Explain neural networks"
}
```

### 7.4 QuizRecord
```json
{
  "session_id": "abc-123",
  "question": "What is backpropagation?",
  "difficulty": 3,
  "learner_answer": "It's the process of updating weights...",
  "score": 0.8,
  "is_correct": true,
  "feedback": "Good understanding! Consider also mentioning..."
}
```

---

## 8. Tech Stack Decision

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| AI/LLM | Anthropic Claude API (claude-sonnet-4-20250514) | High-quality content generation, JSON-mode support |
| AI SDK | `anthropic` Python SDK | Official, supports streaming |
| Backend | FastAPI | Auto-generates OpenAPI docs, async support, Pydantic integration |
| Async HTTP | `httpx` (AsyncClient) | Non-blocking inter-service calls |
| Server | Uvicorn | ASGI server for FastAPI |
| Validation | Pydantic v2 | Request/response schema enforcement |
| Prompt Templates | Jinja2 | Dynamic system prompt construction |
| Database (Dev) | SQLite + SQLAlchemy | Zero-config, file-based |
| Database (Prod) | Supabase (PostgreSQL) | Same ORM code via SQLAlchemy |
| Migrations | Alembic | Schema management across environments |
| Frontend | Streamlit | Rapid prototyping, Python-native |
| Charts | Plotly | Real-time fatigue gauge |
| Testing | pytest + pytest-asyncio | Async-compatible test suite |
| Deployment | Render.com (backend) + Streamlit Cloud (frontend) | Free tiers, GitHub-connected |

---

## 9. Glossary

| Term | Definition |
|------|-----------|
| **CLT** | Cognitive Load Theory — framework describing working memory limits |
| **Fatigue Score** | Float 0–1 representing cognitive exhaustion level |
| **ReAct Loop** | Reason + Act cycle — agentic pattern for observe-plan-act-reflect |
| **Keystroke Cadence** | Typing rhythm including speed, variance, and pause patterns |
| **Mastery Score** | Exponential moving average of quiz performance on a topic |
| **Mode** | One of four adaptive teaching styles: Detailed, Concise, Analogy, Quiz |
| **SSE** | Server-Sent Events — protocol for streaming LLM tokens to frontend |
