"""Unit tests for SVC-06 · Data Persistence Service."""

import sys
import os
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Use in-memory SQLite for tests
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from services.data_store import DataStore, init_db, engine, Base


class TestDataStore:
    """Tests for the data persistence layer."""

    def setup_method(self):
        """Fresh database for each test."""
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        self.store = DataStore()

    # ── Session tests ───────────────────────────────────────────

    def test_create_session(self):
        r = self.store.create_session("s1", "python")
        assert r["session_id"] == "s1"

    def test_get_session(self):
        self.store.create_session("s2", "math")
        s = self.store.get_session("s2")
        assert s is not None
        assert s["topic"] == "math"

    def test_get_nonexistent_session(self):
        assert self.store.get_session("nope") is None

    # ── Profile tests ───────────────────────────────────────────

    def test_upsert_new_profile(self):
        self.store.upsert_profile("s1", topic="ml", mastery_score=0.6)
        p = self.store.get_profile("s1")
        assert p["mastery_score"] == 0.6
        assert p["topic"] == "ml"

    def test_update_existing_profile(self):
        self.store.upsert_profile("s1", mastery_score=0.3)
        self.store.upsert_profile("s1", mastery_score=0.8)
        p = self.store.get_profile("s1")
        assert p["mastery_score"] == 0.8

    def test_get_nonexistent_profile(self):
        assert self.store.get_profile("nope") is None

    # ── Interaction logging tests ───────────────────────────────

    def test_log_interaction(self):
        r = self.store.log_interaction("s1", "hello", "detailed", 0.2, "FRESH", "content")
        assert r["status"] == "logged"

    def test_session_history_ordered(self):
        self.store.log_interaction("s1", "q1", "detailed", 0.1, "FRESH")
        self.store.log_interaction("s1", "q2", "concise", 0.4, "MODERATE")
        history = self.store.get_session_history("s1")
        assert len(history) == 2
        assert history[0]["mode_used"] == "detailed"
        assert history[1]["mode_used"] == "concise"

    # ── Quiz tests ──────────────────────────────────────────────

    def test_store_quiz_result(self):
        r = self.store.store_quiz_result(
            "s1", "physics", "What is F=ma?", "Newton's 2nd law",
            "Force equals mass times acceleration", 0.9, "Excellent!", 3
        )
        assert r["status"] == "stored"

    def test_quiz_history(self):
        self.store.store_quiz_result("s1", "t1", "q1", "a1", "a1", 0.8, "ok")
        self.store.store_quiz_result("s1", "t1", "q2", "a2", "a2", 0.6, "ok")
        history = self.store.get_quiz_history("s1")
        assert len(history) == 2

    def test_recent_quiz_scores(self):
        for score in [0.9, 0.7, 0.5]:
            self.store.store_quiz_result("s1", "t", "q", "a", "a", score, "f")
        scores = self.store.get_recent_quiz_scores("s1", limit=2)
        assert len(scores) == 2

    # ── Export test ──────────────────────────────────────────────

    def test_export_session(self):
        self.store.create_session("s1", "test")
        self.store.log_interaction("s1", "msg", "detailed", 0.2, "FRESH")
        export = self.store.export_session("s1")
        assert "session" in export
        assert "interactions" in export
        assert "quizzes" in export


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
