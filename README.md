# 🧠 Attention-Aware Study Assistant

> An agentic, cloud-native NLP system that monitors learner cognitive state and adapts teaching content in real time.

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.136-green.svg)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.57-red.svg)](https://streamlit.io)

---

## 🎯 What It Does

Traditional e-learning delivers static content regardless of how tired or focused a learner is. This system **actively monitors your cognitive state** through non-intrusive signals (typing patterns, response times, quiz scores) and **automatically adapts** the teaching style:

| Your State | System Response | Content Style |
|------------|----------------|---------------|
| 🟢 **Fresh** | Detailed Mode | Full explanations with examples |
| 🟡 **Moderate Fatigue** | Concise Mode | Bullet-pointed key facts |
| 🟠 **Tired** | Analogy Mode | Relatable metaphors & stories |
| 🔴 **Exhausted** | Quiz Mode | Quick questions with instant feedback |

### Key Features
- **Real-time fatigue detection** from keystroke cadence, response delay, and quiz trends
- **4 adaptive teaching modes** with Jinja2 prompt templates
- **ReAct agentic loop** (Observe → Reason → Act → Reflect) in the Orchestrator
- **LLM-powered session summaries** with personalized narrative recaps
- **Quiz engine** with semantic answer evaluation and constructive feedback
- **Learner profiling** with exponential moving average mastery tracking
- **Break suggestions** when cognitive exhaustion is detected
- **Session export** as downloadable JSON

---

## 🏗️ Architecture

**7 microservices** communicating through a central **Orchestrator Agent** with a **ReAct (Reason + Act) agentic loop**:

```
Frontend (Streamlit:8501)
    │
    ▼
Orchestrator Agent (:8000) ──── Central Brain (ReAct Loop)
    │
    ├── Attention Monitor (:8001) ── Fatigue Detection (rule-based heuristic)
    ├── Learner Profiler (:8002) ─── Session Memory (EMA mastery tracking)
    ├── Content Adapter (:8003) ──── AI Content Gen (4 modes × Jinja2 templates)
    ├── Quiz Engine (:8004) ──────── Quiz Gen & Semantic Evaluation
    └── Data Store (:8005) ──────── SQLite (dev) / PostgreSQL (prod)
```

### LLM Provider Abstraction
The system supports **multiple LLM backends** through a unified provider layer with automatic fallback:

| Priority | Provider | Setup | Notes |
|----------|----------|-------|-------|
| 1️⃣ | **Google Gemini** | Set `GEMINI_API_KEY` in `.env` | Fastest, recommended |
| 2️⃣ | **Ollama** | `ollama serve` + `ollama pull llama3.1:8b` | Fully offline, no API key needed |
| 3️⃣ | **Anthropic Claude** | Set `ANTHROPIC_API_KEY` in `.env` | Optional fallback |

The system auto-detects the best available provider at startup.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- One of: Gemini API key **OR** Ollama installed **OR** Anthropic API key

### Setup

```bash
# 1. Clone and enter
git clone https://github.com/YOUR_USERNAME/attention-aware-study-assistant.git
cd attention-aware-study-assistant

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/Mac

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure LLM provider
cp .env.example .env
```

### Configure Your LLM Provider (pick one)

**Option A — Google Gemini (recommended):**
```bash
# Edit .env and paste your API key:
GEMINI_API_KEY=your_actual_key_here
```

**Option B — Ollama (offline, no key needed):**
```bash
# Install Ollama from https://ollama.com
ollama serve                  # Start the server
ollama pull llama3.1:8b       # Download a model (~4.9 GB)
# The .env already has OLLAMA_URL set — no further config needed
```

### Run (One-Click)
```bash
# Windows: double-click start.bat, or:
start.bat
```

### Run (Manual)
```bash
# Terminal 1: Start backend (all services on port 8000)
python run_server.py

# Terminal 2: Start frontend
streamlit run frontend/app.py --server.port 8501
```

Open **http://localhost:8501** in your browser.

### Run (Terminal Mode — no UI)
```bash
python -m services.orchestrator
```

---

## 📁 Project Structure

```
attention-aware-study-assistant/
├── services/
│   ├── orchestrator.py        # SVC-05 — ReAct agentic loop, port 8000
│   ├── attention_monitor.py   # SVC-01 — fatigue classification, port 8001
│   ├── learner_profiler.py    # SVC-02 — EMA mastery + LLM insights, port 8002
│   ├── content_adapter.py     # SVC-03 — AI content generation (4 modes), port 8003
│   ├── quiz_engine.py         # SVC-04 — quiz gen & semantic eval, port 8004
│   ├── data_store.py          # SVC-06 — SQLAlchemy persistence, port 8005
│   ├── llm_provider.py        # Unified LLM abstraction (Gemini/Ollama/Claude)
│   └── api.py                 # FastAPI app factories for all services
├── frontend/
│   └── app.py                 # SVC-07 — Streamlit UI with fatigue gauge & telemetry
├── prompts/
│   ├── concise.j2             # Jinja2 prompt templates for each teaching mode
│   ├── detailed.j2
│   ├── analogy.j2
│   └── quiz.j2
├── tests/
│   ├── test_attention.py      # 11 tests — fatigue classifier edge cases
│   ├── test_data_store.py     # 12 tests — SQLite CRUD operations
│   ├── test_orchestrator.py   # 20 tests — ReAct loop, mode selection, history
│   ├── test_quiz_engine.py    # 12 tests — quiz gen, evaluation, scoring
│   └── test_content_adapter.py # 20 tests — templates, mode map, generation
├── docs/
│   ├── requirements_spec.md   # User stories, constraints, NLP pipeline
│   └── architecture.md        # Mermaid diagrams (system, sequence, fatigue)
├── run_server.py              # Single-process dev server (all services)
├── start.bat                  # One-click launcher (Windows)
├── Procfile                   # Cloud deployment (Render.com)
├── .env.example               # Environment template
├── requirements.txt
└── README.md
```

---

## 🧪 Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test files
pytest tests/test_attention.py -v       # Fatigue classifier
pytest tests/test_data_store.py -v      # Database CRUD
pytest tests/test_orchestrator.py -v    # Orchestrator ReAct loop
pytest tests/test_quiz_engine.py -v     # Quiz generation & evaluation
pytest tests/test_content_adapter.py -v # Content modes & templates
```

---

## 📡 API Documentation

When running the backend, interactive API docs are available at:

| Service | URL |
|---------|-----|
| Orchestrator (main) | http://localhost:8000/docs |
| Attention Monitor | http://localhost:8000/attention/docs |
| Learner Profiler | http://localhost:8000/profiler/docs |
| Content Adapter | http://localhost:8000/content/docs |
| Quiz Engine | http://localhost:8000/quiz/docs |
| Data Store | http://localhost:8000/data/docs |

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/interact` | POST | Main entry — sends message + telemetry, gets adaptive content |
| `/submit-answer` | POST | Submit quiz answer for semantic evaluation |
| `/session/summary/{id}` | GET | LLM-generated session recap |
| `/attention/analyze-attention` | POST | Fatigue classification from signals |
| `/profiler/profile/{id}` | GET | Learner profile with mastery & difficulty |
| `/profiler/insights/{id}` | GET | LLM-generated learning insights |
| `/data/export/{id}` | GET | Full session export as JSON |

---

## ☁️ Cloud Deployment

### Render.com (Backend)
1. Connect your GitHub repo
2. Create a new Web Service
3. Set environment variables: `GEMINI_API_KEY`, `DATABASE_URL`
4. Start command: `uvicorn run_server:app --host 0.0.0.0 --port $PORT`

### Streamlit Cloud (Frontend)
1. Connect your GitHub repo
2. Set `frontend/app.py` as the main file
3. Add secrets in Streamlit Cloud settings

---

## 🤖 GenAI Usage Reflection

### What Worked Well
- **LLM abstraction layer** made switching between Gemini/Ollama/Claude seamless — zero code changes needed
- **Jinja2 prompt templates** for the 4 teaching modes produced high-quality, differentiated content
- **JSON-schema enforcement** with retry logic for quiz generation ensured structured LLM outputs
- **ReAct agentic loop** provided clean separation of observe/reason/act/reflect responsibilities
- **Ollama integration** enabled fully offline development with local models

### Where It Fell Short
- LLMs occasionally output markdown-wrapped JSON despite explicit instructions (solved with multi-layer parsing)
- Streaming responses (SSE) require additional complexity for real-time token display
- Keystroke telemetry is simulated in the Streamlit UI — real JS tracking needs Streamlit Components
- Small local models (e.g., llama3.1:8b) sometimes produce lower-quality quiz JSON than cloud models

### Overall Impact
GenAI tools were instrumental in every phase — from researching cognitive load theory, to drafting architecture, to generating service code and prompt templates. The LLM provider abstraction layer was the key architectural decision, enabling development with local models while supporting cloud deployment with stronger models. Estimated **60% of development time was saved** through AI-assisted coding.

---

## 📄 License

MIT License — Built for the GenAI System Building Challenge Lab Hackathon.
