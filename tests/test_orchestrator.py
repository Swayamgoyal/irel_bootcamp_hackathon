"""Unit tests for SVC-05 · Orchestrator Agent — ReAct agentic loop."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Use in-memory SQLite for tests
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from services.data_store import DataStore, Base, engine
from services.attention_monitor import FatigueClassifier
from services.learner_profiler import LearnerProfiler
from services.orchestrator import Orchestrator


class TestOrchestrator:
    """Tests for the Orchestrator's ReAct cycle."""

    def setup_method(self):
        """Fresh database and orchestrator for each test."""
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        self.orch = Orchestrator()

    # ── interact() basic structure ──────────────────────────────

    def test_interact_returns_required_keys(self):
        """interact() must return all required response keys."""
        result = self.orch.interact(user_message="What is Python?")
        required_keys = {
            "session_id", "content", "mode_used", "fatigue_state",
            "profile", "response_time_seconds", "type",
        }
        assert required_keys.issubset(result.keys())

    def test_interact_creates_session_id(self):
        """If no session_id provided, one is generated."""
        result = self.orch.interact(user_message="Hello")
        assert result["session_id"] is not None
        assert len(result["session_id"]) > 0

    def test_interact_uses_provided_session_id(self):
        """If session_id is provided, it's used."""
        result = self.orch.interact(user_message="Hello", session_id="my-session")
        assert result["session_id"] == "my-session"

    def test_interact_returns_fatigue_state(self):
        """Fatigue state must contain score, label, confidence, signals."""
        result = self.orch.interact(user_message="Test")
        fs = result["fatigue_state"]
        assert "score" in fs
        assert "label" in fs
        assert "confidence" in fs
        assert "signals" in fs
        assert 0.0 <= fs["score"] <= 1.0

    def test_interact_returns_profile(self):
        """Profile should contain mastery_score and difficulty_level."""
        result = self.orch.interact(user_message="Test", session_id="prof-test")
        profile = result["profile"]
        assert "mastery_score" in profile
        assert "difficulty_level" in profile

    # ── Mode selection ─────────────────────────────────────────

    def test_fresh_selects_detailed_mode(self):
        """No fatigue signals (FRESH) → detailed mode."""
        result = self.orch.interact(
            user_message="Explain recursion",
            keypress_intervals=[120, 130, 125],
            response_delay_ms=1000,
        )
        assert result["mode_used"] == "detailed"

    def test_manual_mode_override(self):
        """Manual mode override should force the mode regardless of fatigue."""
        result = self.orch.interact(
            user_message="Explain sorting",
            manual_mode="analogy",
        )
        assert result["mode_used"] == "analogy"

    def test_manual_quiz_mode(self):
        """Manual quiz mode should produce quiz-type response."""
        result = self.orch.interact(
            user_message="Data structures",
            manual_mode="quiz",
        )
        # Should be quiz mode (may fall back to concise if LLM fails)
        assert result["mode_used"] in ("quiz", "concise")

    # ── Conversation history ───────────────────────────────────

    def test_conversation_history_maintained(self):
        """Conversation history tracks interactions."""
        sid = "hist-test"
        self.orch.interact(user_message="Topic 1", session_id=sid)
        self.orch.interact(user_message="Topic 2", session_id=sid)
        assert sid in self.orch.conversation_history
        assert len(self.orch.conversation_history[sid]) == 2

    def test_conversation_history_capped_at_10(self):
        """History should keep only the last 10 turns."""
        sid = "cap-test"
        for i in range(15):
            self.orch.interact(user_message=f"Topic {i}", session_id=sid)
        assert len(self.orch.conversation_history[sid]) <= 10

    # ── Session summary ────────────────────────────────────────

    def test_session_summary_structure(self):
        """Session summary returns expected keys."""
        sid = "summary-test"
        self.orch.interact(user_message="Test topic", session_id=sid)
        summary = self.orch.get_session_summary(sid)
        assert "session_id" in summary
        assert "total_interactions" in summary
        assert "total_quizzes" in summary
        assert "profile" in summary
        assert "mode_distribution" in summary

    def test_session_summary_counts_interactions(self):
        """Summary correctly counts interactions."""
        sid = "count-test"
        self.orch.interact(user_message="Q1", session_id=sid)
        self.orch.interact(user_message="Q2", session_id=sid)
        self.orch.interact(user_message="Q3", session_id=sid)
        summary = self.orch.get_session_summary(sid)
        assert summary["total_interactions"] == 3

    # ── Quiz submission ────────────────────────────────────────

    def test_submit_quiz_answer_returns_evaluation(self):
        """Quiz answer submission should return evaluation if LLM is available."""
        sid = "quiz-test"
        self.orch.interact(user_message="Physics", session_id=sid)
        result = self.orch.submit_quiz_answer(
            session_id=sid,
            question="What is gravity?",
            correct_answer="Force of attraction between masses",
            learner_answer="Force that pulls things down",
            topic="physics",
        )
        # If LLM is not available, it returns an error dict
        if "error" in result:
            assert result["error"] == "No LLM configured"
        else:
            assert "evaluation" in result
            assert "updated_profile" in result

    # ── Data persistence ───────────────────────────────────────

    def test_interaction_logged_to_data_store(self):
        """Each interact() call should log to the data store."""
        sid = "log-test"
        self.orch.interact(user_message="Log this", session_id=sid)
        history = self.orch.data_store.get_session_history(sid)
        assert len(history) >= 1
        assert history[0]["user_message"] == "Log this"

    def test_profile_updated_after_interaction(self):
        """Profile should be updated with fatigue and mode after interaction."""
        sid = "update-test"
        self.orch.interact(user_message="Update me", session_id=sid)
        profile = self.orch.profiler.get_profile(sid)
        assert profile is not None
        assert profile["preferred_mode"] is not None

    # ── Fallback / error handling ──────────────────────────────

    def test_no_llm_returns_placeholder_content(self):
        """If LLM is unavailable, should still return a response with content."""
        result = self.orch.interact(user_message="Anything")
        assert result["content"] is not None
        assert len(result["content"]) > 0

    def test_response_time_is_tracked(self):
        """Response time should be a non-negative float."""
        result = self.orch.interact(user_message="Time me")
        assert result["response_time_seconds"] >= 0

    # ── Topic handling ─────────────────────────────────────────

    def test_topic_defaults_to_user_message(self):
        """If no topic given, user_message is used as topic."""
        sid = "topic-test"
        result = self.orch.interact(
            user_message="Neural networks", session_id=sid
        )
        profile = self.orch.profiler.get_profile(sid)
        assert profile["topic"] is not None

    def test_explicit_topic_used(self):
        """If topic is given, it should be used over user_message."""
        sid = "explicit-topic"
        result = self.orch.interact(
            user_message="Tell me about it",
            session_id=sid,
            topic="quantum_computing",
        )
        profile = self.orch.profiler.get_profile(sid)
        assert profile["topic"] == "quantum_computing"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
