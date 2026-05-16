# 📋 Complete Project Documentation
# Attention-Aware Study Assistant — Setup, Run & Architecture Guide

---

## 🚀 How to Run the Project

### Prerequisites
- **Python 3.10+** installed
- **Ollama** installed (for offline LLM) OR a **Google Gemini API key**

### Step-by-Step Setup

```bash
# 1. Clone/navigate to the project
cd irel_bootcamp_hackathon

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
venv\Scripts\activate          # Windows (PowerShell/CMD)
# source venv/bin/activate     # Linux/Mac

# 4. Install all dependencies
pip install -r requirements.txt

# 5. Create your .env file from the template
cp .env.example .env
# Then edit .env and add your GEMINI_API_KEY (or leave empty to use Ollama)
```

### Running the Application

**Option 1 — One-Click (Windows CMD):**
```bash
# In CMD (not PowerShell):
start.bat

# In PowerShell use:
.\start.bat
```

**Option 2 — Manual (two terminals):**
```bash
# Terminal 1: Start the backend API server (all 6 services on port 8000)
venv\Scripts\python run_server.py

# Terminal 2: Start the Streamlit frontend
venv\Scripts\streamlit run frontend/app.py --server.port 8501
```

**Option 3 — Terminal Mode (no UI, just CLI):**
```bash
venv\Scripts\python -m services.orchestrator
```

### Accessing the Application

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:8501 | Streamlit UI — main user interface |
| **API Docs** | http://localhost:8000/docs | Swagger/OpenAPI interactive docs |
| **Attention Monitor** | http://localhost:8000/attention/docs | Fatigue classification API |
| **Learner Profiler** | http://localhost:8000/profiler/docs | Profile management API |
| **Content Adapter** | http://localhost:8000/content/docs | Content generation API |
| **Quiz Engine** | http://localhost:8000/quiz/docs | Quiz gen & evaluation API |
| **Data Store** | http://localhost:8000/data/docs | Persistence layer API |

---

## 🏛️ Architecture Overview

### System Architecture

The system implements a **ReAct (Reason + Act) agentic loop** through 7 microservices:

```
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND (Streamlit :8501)                     │
│   Text Input → Keypress Telemetry → Fatigue Gauge → Quiz UI     │
└──────────────────────────┬──────────────────────────────────────┘
                           │ POST /interact
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                ORCHESTRATOR AGENT (:8000)                         │
│                                                                   │
│   1. OBSERVE  → Collect user message + telemetry                 │
│   2. REASON   → Call Attention Monitor + Learner Profiler        │
│   3. ACT      → Dispatch to Content Adapter OR Quiz Engine      │
│   4. REFLECT  → Update profile, log interaction                  │
└──────┬──────────┬──────────┬──────────┬──────────┬──────────────┘
       │          │          │          │          │
       ▼          ▼          ▼          ▼          ▼
  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
  │Attention│ │Learner │ │Content │ │  Quiz  │ │  Data  │
  │Monitor │ │Profiler│ │Adapter │ │ Engine │ │ Store  │
  │ :8001  │ │ :8002  │ │ :8003  │ │ :8004  │ │ :8005  │
  └────────┘ └────────┘ └───┬────┘ └───┬────┘ └────────┘
                            │          │
                            ▼          ▼
                    ┌─────────────────────┐
                    │   LLM Provider      │
                    │ Gemini → Ollama →   │
                    │ Anthropic (fallback)│
                    └─────────────────────┘
```

### Service Descriptions

| # | Service | File | Port | Role |
|---|---------|------|------|------|
| SVC-01 | **Attention Monitor** | `services/attention_monitor.py` | 8001 | Classifies fatigue from keystroke cadence, response delay, quiz trends |
| SVC-02 | **Learner Profiler** | `services/learner_profiler.py` | 8002 | Tracks mastery (EMA), difficulty, preferred mode, generates insights |
| SVC-03 | **Content Adapter** | `services/content_adapter.py` | 8003 | Generates adaptive content in 4 modes using Jinja2 + LLM |
| SVC-04 | **Quiz Engine** | `services/quiz_engine.py` | 8004 | Generates MCQ/open-ended questions, evaluates answers semantically |
| SVC-05 | **Orchestrator** | `services/orchestrator.py` | 8000 | Central brain — ReAct loop, mode decision, coordinates all agents |
| SVC-06 | **Data Store** | `services/data_store.py` | 8005 | SQLAlchemy persistence (sessions, interactions, profiles, quizzes) |
| SVC-07 | **Frontend** | `frontend/app.py` | 8501 | Streamlit UI with fatigue gauge, quiz interface, session management |

### Supporting Files

| File | Purpose |
|------|---------|
| `services/llm_provider.py` | Unified LLM abstraction — Gemini/Ollama/Anthropic with auto-detection |
| `services/api.py` | FastAPI app factories — creates REST endpoints for all services |
| `run_server.py` | Development server — mounts all services under single port 8000 |
| `start.bat` | One-click launcher for Windows (starts backend + frontend) |
| `Procfile` | Cloud deployment config for Render.com |

---

## 🧠 Four Adaptive Teaching Modes

| Learner State | Fatigue Score | Mode Selected | Content Style | Prompt Template |
|---------------|---------------|---------------|---------------|-----------------|
| 🟢 FRESH | 0.00 – 0.25 | **Detailed** | Full explanations, examples, step-by-step | `prompts/detailed.j2` |
| 🟡 MODERATE | 0.25 – 0.50 | **Concise** | ≤5 bullet points, key facts only | `prompts/concise.j2` |
| 🟠 TIRED | 0.50 – 0.75 | **Analogy** | Metaphors, stories, "explain like I'm 10" | `prompts/analogy.j2` |
| 🔴 EXHAUSTED | 0.75 – 1.00 | **Quiz** | Single question with instant feedback | `prompts/quiz.j2` |

---

## 📊 Fatigue Detection Algorithm

Three input signals, weighted and combined:

```
Signal                    Weight    How It's Measured
─────────────────────     ──────    ────────────────────────────────
Keystroke Variance        40%       Slowness + irregularity of typing
Response Delay            30%       Time to respond (normalized 3s-30s)
Quiz Score Trend          30%       Decline in recent quiz scores

Final Score = Σ(weight × signal_score) / Σ(weights_used)
```

Classification thresholds:
- **FRESH**: 0.00 – 0.25
- **MODERATE**: 0.25 – 0.50
- **TIRED**: 0.50 – 0.75
- **EXHAUSTED**: 0.75 – 1.00

---

## 🔌 LLM Provider System

The system auto-detects the best available LLM at startup:

```
Priority Chain: Gemini → Ollama → Anthropic → None (placeholder mode)
```

| Provider | Config | Speed | Offline? |
|----------|--------|-------|----------|
| **Gemini Flash 2.5** | Set `GEMINI_API_KEY` in `.env` | ~2-5s per call | No |
| **Ollama (llama3.1:8b)** | `ollama serve` running | ~15-30s per call | Yes ✅ |
| **Anthropic Claude** | Set `ANTHROPIC_API_KEY` in `.env` | ~3-5s per call | No |

Features:
- **Auto-detection**: Finds the best provider at startup
- **Rate limit retry**: Gemini retries up to 3× on 429 errors (15s backoff)
- **JSON parsing**: Multi-layer parser handles markdown-wrapped JSON from LLMs
- **Fallback**: If no LLM available, returns placeholder content

---

## 🗄️ Database Schema

Four SQLite tables managed by SQLAlchemy ORM:

| Table | Key Columns | Purpose |
|-------|-------------|---------|
| `sessions` | id, start_time, topic, status | Track study sessions |
| `interactions` | session_id, mode_used, fatigue_score, content_snippet | Log every interaction |
| `learner_profiles` | session_id, mastery_score, preferred_mode, difficulty | Persistent learner model |
| `quiz_records` | session_id, question, correct_answer, score, feedback | Quiz history |

---

## 🧪 Test Suite

### Running Tests

```bash
# Fast unit tests (no LLM needed, runs in ~2 seconds)
venv\Scripts\pytest tests/test_attention.py tests/test_data_store.py -v

# All unit tests (no LLM calls, ~3 seconds)
venv\Scripts\pytest tests/test_attention.py tests/test_data_store.py tests/test_content_adapter.py::TestModeSelection tests/test_content_adapter.py::TestPromptRendering tests/test_content_adapter.py::TestModeMap tests/test_quiz_engine.py::TestQuizEngineUnit -v

# Full suite including LLM tests (requires Ollama/Gemini, takes longer)
venv\Scripts\pytest tests/ -v
```

### Test Coverage

| Test File | # Tests | What's Tested |
|-----------|---------|---------------|
| `test_attention.py` | 11 | Fatigue classification: labels, scores, confidence, edge cases |
| `test_data_store.py` | 12 | SQLite CRUD: sessions, profiles, interactions, quizzes, export |
| `test_content_adapter.py` | 20 | Mode selection (8), template rendering (6), generation (4), MODE_MAP (2) |
| `test_orchestrator.py` | 19 | ReAct loop, mode override, history, summary, persistence, fallback |
| `test_quiz_engine.py` | 12 | MCQ/open-ended gen, answer evaluation, score ranges |
| **Total** | **74** | |

> **Note**: LLM-dependent tests may be slow with Gemini free tier (5 req/min limit).
> Tests pass individually but may timeout in batch runs due to rate limiting.

---

## 📂 Complete File Tree

```
irel_bootcamp_hackathon/
│
├── services/                        # Backend microservices
│   ├── __init__.py
│   ├── orchestrator.py              # SVC-05: ReAct loop, session summary
│   ├── attention_monitor.py         # SVC-01: Fatigue classifier (rule-based)
│   ├── learner_profiler.py          # SVC-02: EMA mastery, insights
│   ├── content_adapter.py           # SVC-03: 4-mode content gen
│   ├── quiz_engine.py               # SVC-04: Quiz gen + semantic eval
│   ├── data_store.py                # SVC-06: SQLAlchemy ORM
│   ├── llm_provider.py              # Unified LLM (Gemini/Ollama/Claude)
│   └── api.py                       # FastAPI route factories
│
├── frontend/
│   └── app.py                       # SVC-07: Streamlit UI
│
├── prompts/                         # Jinja2 prompt templates
│   ├── detailed.j2                  # Full explanation mode
│   ├── concise.j2                   # Bullet-point mode
│   ├── analogy.j2                   # Metaphor/story mode
│   └── quiz.j2                      # Question generation mode
│
├── tests/                           # Pytest test suite (74 tests)
│   ├── __init__.py
│   ├── test_attention.py            # 11 tests
│   ├── test_data_store.py           # 12 tests
│   ├── test_content_adapter.py      # 20 tests
│   ├── test_orchestrator.py         # 19 tests
│   └── test_quiz_engine.py          # 12 tests
│
├── docs/
│   ├── requirements_spec.md         # User stories, constraints
│   ├── architecture.md              # Mermaid diagrams
│   └── project_documentation.md     # THIS FILE
│
├── data/                            # SQLite database (auto-created)
│
├── run_server.py                    # Dev server (all services on :8000)
├── start.bat                        # Windows launcher
├── Procfile                         # Cloud deploy (Render.com)
├── runtime.txt                      # Python version for cloud
├── requirements.txt                 # pip dependencies
├── .env                             # Local config (gitignored!)
├── .env.example                     # Config template (safe to commit)
├── .gitignore                       # Git exclusions
└── README.md                        # Project overview
```

---

## 📡 API Reference

### POST /interact — Main Entry Point
```json
// Request
{
    "user_message": "Explain neural networks",
    "session_id": "abc-123",          // optional, auto-generated
    "topic": "machine_learning",      // optional
    "keypress_intervals": [130, 140], // optional, ms between keypresses
    "response_delay_ms": 3000,        // optional
    "manual_mode": "analogy"          // optional: force a specific mode
}

// Response
{
    "session_id": "abc-123",
    "content": "Neural networks are like...",  // Markdown content
    "mode_used": "analogy",
    "type": "content",
    "fatigue_state": {
        "score": 0.62,
        "label": "TIRED",
        "confidence": 1.0,
        "signals": {"keypress_variance": 0.7, "response_delay_norm": 0.5, "quiz_trend": null}
    },
    "profile": {
        "session_id": "abc-123",
        "mastery_score": 0.45,
        "difficulty_level": 3,
        "preferred_mode": "analogy"
    },
    "response_time_seconds": 5.2
}
```

### POST /submit-answer — Quiz Evaluation
```json
// Request
{
    "session_id": "abc-123",
    "question": "What is backpropagation?",
    "correct_answer": "Algorithm for computing gradients",
    "learner_answer": "It's how networks learn by going backwards",
    "topic": "neural_networks"
}

// Response
{
    "evaluation": {
        "score": 0.75,
        "is_correct": true,
        "feedback": "Good understanding! Consider also mentioning gradient descent."
    },
    "updated_profile": { "mastery_score": 0.52, ... }
}
```

### GET /session/summary/{session_id}
Returns stats + LLM-generated narrative recap of the session.

### GET /profiler/insights/{session_id}
Returns LLM-generated learning insights and recommendations.

### GET /data/export/{session_id}
Returns full session data as downloadable JSON.

---

## ☁️ Cloud Deployment

### Render.com (Backend)
1. Connect GitHub repo
2. Create Web Service
3. Set env vars: `GEMINI_API_KEY`, `DATABASE_URL`
4. Start command: `uvicorn run_server:app --host 0.0.0.0 --port $PORT`

### Streamlit Cloud (Frontend)
1. Connect GitHub repo
2. Main file: `frontend/app.py`
3. Add secrets in Streamlit Cloud settings

---

## 🤖 GenAI Usage Reflection

### What Worked Well
- **LLM abstraction layer** — switching between Gemini/Ollama/Claude requires zero code changes
- **Jinja2 prompt templates** — 4 distinct teaching modes produce genuinely different content
- **JSON-schema enforcement** with retry logic for quiz generation
- **ReAct agentic loop** — clean Observe→Reason→Act→Reflect separation
- **Ollama integration** — enabled fully offline development with local models

### Where It Fell Short
- Gemini free tier rate limits (5 req/min) cause issues during testing
- LLMs occasionally wrap JSON in markdown code blocks (solved with multi-layer parser)
- Keystroke telemetry is simulated in Streamlit (real JS tracking needs Streamlit Components)
- Local models (llama3.1:8b) are slower and produce lower quality than cloud models

### Overall Impact
GenAI tools were instrumental across all phases:
- Research: cognitive load theory, keystroke dynamics literature
- Architecture: microservice design, data flow diagrams
- Implementation: service code, prompt templates, test suites
- **Estimated 60% development time saved** through AI-assisted coding
