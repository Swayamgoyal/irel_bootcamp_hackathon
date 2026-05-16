# Attention-Aware Study Assistant — Architecture Diagram
# 
# This file contains a Mermaid diagram of the system architecture.
# Render it at: https://mermaid.live or in any Markdown viewer that supports Mermaid.
#
# Alternatively, open this in Excalidraw and trace over it for a polished hand-drawn look.

```mermaid
graph TB
    subgraph "Frontend Layer"
        FE["🖥️ Streamlit Frontend<br/>Port 8501<br/>SVC-07"]
    end

    subgraph "Orchestration Layer"
        ORC["🧠 Orchestrator Agent<br/>Port 8000<br/>SVC-05<br/><i>ReAct Loop: Observe → Reason → Act → Reflect</i>"]
    end

    subgraph "Perception Layer"
        ATT["👁️ Attention Monitor<br/>Port 8001<br/>SVC-01<br/><i>Fatigue Classification</i>"]
        LP["📊 Learner Profiler<br/>Port 8002<br/>SVC-02<br/><i>Session Memory</i>"]
    end

    subgraph "Action Layer"
        CA["📝 Content Adapter<br/>Port 8003<br/>SVC-03<br/><i>4 Teaching Modes</i>"]
        QE["❓ Quiz Engine<br/>Port 8004<br/>SVC-04<br/><i>Generate & Evaluate</i>"]
    end

    subgraph "Infrastructure Layer"
        DS["💾 Data Persistence<br/>Port 8005<br/>SVC-06<br/><i>SQLite / PostgreSQL</i>"]
    end

    subgraph "External"
        CLAUDE["☁️ Anthropic Claude API<br/>claude-sonnet-4-20250514"]
    end

    FE -->|"POST /interact<br/>+ keypress telemetry"| ORC

    ORC -->|"POST /analyze-attention<br/>(concurrent)"| ATT
    ORC -->|"GET /profile/{session_id}<br/>(concurrent)"| LP

    ORC -->|"POST /generate-content<br/>(if content mode)"| CA
    ORC -->|"POST /generate-quiz<br/>(if quiz mode)"| QE

    ORC -->|"POST /store<br/>POST /profile/update"| DS
    ATT -->|"POST /store"| DS
    LP -->|"read/write profiles"| DS

    CA -->|"API call<br/>(streaming)"| CLAUDE
    QE -->|"API call<br/>(JSON mode)"| CLAUDE

    ORC -->|"Streamed response<br/>(SSE)"| FE

    style FE fill:#FF6B6B,stroke:#333,color:#fff
    style ORC fill:#4ECDC4,stroke:#333,color:#fff
    style ATT fill:#45B7D1,stroke:#333,color:#fff
    style LP fill:#45B7D1,stroke:#333,color:#fff
    style CA fill:#96CEB4,stroke:#333,color:#fff
    style QE fill:#96CEB4,stroke:#333,color:#fff
    style DS fill:#FFEAA7,stroke:#333,color:#333
    style CLAUDE fill:#DDA0DD,stroke:#333,color:#333
```

## Data Flow — Single Interaction Cycle

```mermaid
sequenceDiagram
    participant U as 👤 Learner
    participant FE as 🖥️ Frontend
    participant ORC as 🧠 Orchestrator
    participant ATT as 👁️ Attention Monitor
    participant LP as 📊 Learner Profiler
    participant CA as 📝 Content Adapter
    participant QE as ❓ Quiz Engine
    participant DS as 💾 Data Store
    participant AI as ☁️ Claude API

    U->>FE: Types topic + question
    Note over FE: JS captures keypress<br/>timestamps
    FE->>ORC: POST /interact {message, session_id, telemetry}
    
    par Concurrent Calls
        ORC->>ATT: POST /analyze-attention {keypress_intervals, response_delay, quiz_scores}
        ATT-->>ORC: {score: 0.62, label: "TIRED", confidence: 0.85}
        ORC->>LP: GET /profile/{session_id}
        LP-->>ORC: {mastery: 0.45, preferred_mode: "analogy", difficulty: 3}
    end

    Note over ORC: REASON: TIRED → Analogy Mode

    alt Analogy/Concise/Detailed Mode
        ORC->>CA: POST /generate-content {topic, fatigue_label, profile, mode}
        CA->>AI: Claude API (streaming, analogy.j2 template)
        AI-->>CA: Streamed tokens
        CA-->>ORC: {content: "Think of it like...", mode: "analogy", read_time: 45}
    else Quiz Mode
        ORC->>QE: POST /generate-quiz {topic, difficulty}
        QE->>AI: Claude API (JSON mode)
        AI-->>QE: {question, options, correct_answer}
        QE-->>ORC: Quiz payload
    end

    ORC->>LP: POST /profile/update {quiz_result, mode_used}
    ORC->>DS: POST /store {interaction_log}
    ORC-->>FE: Streamed adaptive content (SSE)
    FE-->>U: Rendered Markdown + fatigue gauge update
```

## Fatigue Classification Logic

```mermaid
graph LR
    subgraph "Input Signals"
        KP["⌨️ Keypress Intervals"]
        RD["⏱️ Response Delay"]
        QS["📉 Quiz Score Trend"]
    end

    subgraph "Weighted Heuristic"
        W["Score = 0.4×keypress_var +<br/>0.3×delay_norm +<br/>0.3×quiz_decline"]
    end

    subgraph "Classification"
        F["🟢 FRESH<br/>0.00 – 0.25"]
        M["🟡 MODERATE<br/>0.25 – 0.50"]
        T["🟠 TIRED<br/>0.50 – 0.75"]
        E["🔴 EXHAUSTED<br/>0.75 – 1.00"]
    end

    KP --> W
    RD --> W
    QS --> W
    W --> F
    W --> M
    W --> T
    W --> E

    style F fill:#27AE60,color:#fff
    style M fill:#F39C12,color:#fff
    style T fill:#E67E22,color:#fff
    style E fill:#E74C3C,color:#fff
```
