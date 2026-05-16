"""
FastAPI Application Factory

Creates FastAPI app instances for each microservice.
Phase 2: Wraps Phase 1 modules as REST APIs.
"""

# ─── SVC-01: Attention Monitor API (Port 8001) ─────────────────────────
def create_attention_app():
    from fastapi import FastAPI
    from pydantic import BaseModel
    from typing import Optional, List
    from services.attention_monitor import FatigueClassifier

    app = FastAPI(title="Attention Monitor Agent", version="1.0", docs_url="/docs")
    classifier = FatigueClassifier()

    class AttentionRequest(BaseModel):
        keypress_intervals: Optional[List[float]] = None
        response_delay_ms: Optional[int] = None
        recent_quiz_scores: Optional[List[float]] = None

    class FatigueResponse(BaseModel):
        score: float
        label: str
        confidence: float
        signals: dict

    @app.post("/analyze-attention", response_model=FatigueResponse)
    def analyze(req: AttentionRequest):
        result = classifier.classify(
            keypress_intervals=req.keypress_intervals,
            response_delay_ms=req.response_delay_ms,
            recent_quiz_scores=req.recent_quiz_scores,
        )
        return result.to_dict()

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "attention_monitor"}

    return app


# ─── SVC-02: Learner Profiler API (Port 8002) ──────────────────────────
def create_profiler_app():
    from fastapi import FastAPI
    from pydantic import BaseModel
    from typing import Optional
    from services.learner_profiler import LearnerProfiler

    app = FastAPI(title="Learner Profiler Agent", version="1.0", docs_url="/docs")
    profiler = LearnerProfiler()

    class ProfileUpdateRequest(BaseModel):
        session_id: str
        mode_used: Optional[str] = None
        fatigue_score: Optional[float] = None
        quiz_score: Optional[float] = None
        topic: Optional[str] = None

    @app.get("/profile/{session_id}")
    def get_profile(session_id: str):
        return profiler.get_profile(session_id)

    @app.post("/profile/update")
    def update_profile(req: ProfileUpdateRequest):
        if req.quiz_score is not None:
            return profiler.update_after_quiz(req.session_id, req.quiz_score, req.fatigue_score or 0)
        elif req.mode_used:
            return profiler.update_after_interaction(
                req.session_id, req.mode_used, req.fatigue_score or 0, req.topic
            )
        return {"error": "Provide mode_used or quiz_score"}

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "learner_profiler"}

    @app.get("/insights/{session_id}")
    def insights(session_id: str):
        return profiler.get_insights(session_id)

    return app


# ─── SVC-03: Content Adapter API (Port 8003) ───────────────────────────
def create_content_app():
    from fastapi import FastAPI
    from pydantic import BaseModel
    from typing import Optional
    from services.content_adapter import ContentAdapter

    app = FastAPI(title="Content Adaptation Agent", version="1.0", docs_url="/docs")
    adapter = ContentAdapter()

    class ContentRequest(BaseModel):
        topic: str
        fatigue_label: str = "FRESH"
        mastery_level: int = 2
        difficulty: int = 2
        manual_mode: Optional[str] = None

    @app.post("/generate-content")
    def generate(req: ContentRequest):
        return adapter.generate_content(
            topic=req.topic, fatigue_label=req.fatigue_label,
            mastery_level=req.mastery_level, difficulty=req.difficulty,
            manual_mode=req.manual_mode,
        )

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "content_adapter", "llm": adapter.llm.get_info()}

    return app


# ─── SVC-04: Quiz Engine API (Port 8004) ───────────────────────────────
def create_quiz_app():
    from fastapi import FastAPI
    from pydantic import BaseModel
    from services.quiz_engine import QuizEngine

    app = FastAPI(title="Quiz Engine Agent", version="1.0", docs_url="/docs")
    engine = QuizEngine()

    class QuizGenRequest(BaseModel):
        topic: str
        difficulty: int = 2

    class AnswerEvalRequest(BaseModel):
        question: str
        correct_answer: str
        learner_answer: str

    @app.post("/generate-quiz")
    def generate_quiz(req: QuizGenRequest):
        return engine.generate_quiz(req.topic, req.difficulty)

    @app.post("/evaluate-answer")
    def evaluate(req: AnswerEvalRequest):
        return engine.evaluate_answer(req.question, req.correct_answer, req.learner_answer)

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "quiz_engine", "llm": engine.llm.get_info()}

    return app


# ─── SVC-05: Orchestrator API (Port 8000) ──────────────────────────────
def create_orchestrator_app():
    from fastapi import FastAPI
    from pydantic import BaseModel
    from typing import Optional, List
    from services.orchestrator import Orchestrator

    app = FastAPI(title="Orchestrator Agent", version="1.0", docs_url="/docs")
    orch = Orchestrator()

    class InteractRequest(BaseModel):
        user_message: str
        session_id: Optional[str] = None
        topic: Optional[str] = None
        keypress_intervals: Optional[List[float]] = None
        response_delay_ms: Optional[int] = None
        manual_mode: Optional[str] = None

    class QuizAnswerRequest(BaseModel):
        session_id: str
        question: str
        correct_answer: str
        learner_answer: str
        topic: str = ""

    @app.post("/interact")
    def interact(req: InteractRequest):
        return orch.interact(
            user_message=req.user_message,
            session_id=req.session_id,
            topic=req.topic,
            keypress_intervals=req.keypress_intervals,
            response_delay_ms=req.response_delay_ms,
            manual_mode=req.manual_mode,
        )

    @app.post("/submit-answer")
    def submit_answer(req: QuizAnswerRequest):
        return orch.submit_quiz_answer(
            req.session_id, req.question, req.correct_answer,
            req.learner_answer, req.topic,
        )

    @app.get("/session/summary/{session_id}")
    def session_summary(session_id: str):
        return orch.get_session_summary(session_id)

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "orchestrator", "llm": orch.content_adapter.llm.get_info()}

    return app


# ─── SVC-06: Data Store API (Port 8005) ────────────────────────────────
def create_data_store_app():
    from fastapi import FastAPI
    from pydantic import BaseModel
    from typing import Optional
    from services.data_store import DataStore

    app = FastAPI(title="Data Persistence Service", version="1.0", docs_url="/docs")
    store = DataStore()

    class StoreRequest(BaseModel):
        entity_type: str  # "session", "interaction", "profile", "quiz"
        session_id: str
        payload: dict = {}

    @app.post("/store")
    def store_data(req: StoreRequest):
        if req.entity_type == "session":
            return store.create_session(req.session_id, req.payload.get("topic"))
        elif req.entity_type == "interaction":
            return store.log_interaction(req.session_id, **req.payload)
        elif req.entity_type == "profile":
            return store.upsert_profile(req.session_id, **req.payload)
        elif req.entity_type == "quiz":
            return store.store_quiz_result(session_id=req.session_id, **req.payload)
        return {"error": f"Unknown entity_type: {req.entity_type}"}

    @app.get("/session-history/{session_id}")
    def session_history(session_id: str):
        return store.get_session_history(session_id)

    @app.get("/export/{session_id}")
    def export_session(session_id: str):
        return store.export_session(session_id)

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "data_store"}

    return app
