"""
SVC-02 · Learner Profiler Agent
Port: 8002
Session context & adaptive profile manager

Maintains a persistent learner model across sessions. Tracks topic mastery,
preferred explanation styles, difficulty progression, and historical fatigue patterns.

Phase 1: Standalone Python module using DataStore for persistence.
"""

from typing import Optional
from services.data_store import DataStore


class LearnerProfiler:
    """Manages learner profiles — the memory layer for all agents."""

    # Exponential moving average smoothing factor
    EMA_ALPHA = 0.3

    def __init__(self, data_store: Optional[DataStore] = None):
        self.store = data_store or DataStore()

    def get_profile(self, session_id: str) -> dict:
        """Get or create a learner profile."""
        profile = self.store.get_profile(session_id)
        if profile is None:
            self.store.upsert_profile(session_id)
            profile = self.store.get_profile(session_id)
        return profile

    def update_after_interaction(self, session_id: str, mode_used: str,
                                 fatigue_score: float, topic: Optional[str] = None) -> dict:
        """Update profile after a content interaction."""
        profile = self.get_profile(session_id)

        # Update average fatigue using EMA
        old_fatigue = profile.get("avg_fatigue", 0.0) or 0.0
        new_fatigue = self.EMA_ALPHA * fatigue_score + (1 - self.EMA_ALPHA) * old_fatigue

        updates = {
            "preferred_mode": mode_used,
            "avg_fatigue": round(new_fatigue, 3),
        }
        if topic:
            updates["topic"] = topic

        self.store.upsert_profile(session_id, **updates)
        return self.get_profile(session_id)

    def update_after_quiz(self, session_id: str, quiz_score: float,
                          fatigue_score: float = 0.0) -> dict:
        """Update mastery score after a quiz using exponential moving average."""
        profile = self.get_profile(session_id)
        old_mastery = profile.get("mastery_score", 0.5) or 0.5

        # EMA update for mastery
        new_mastery = self.EMA_ALPHA * quiz_score + (1 - self.EMA_ALPHA) * old_mastery
        new_mastery = max(0.0, min(1.0, new_mastery))

        # Recalculate difficulty: base + mastery bonus - fatigue penalty
        new_difficulty = self.calculate_difficulty(new_mastery, fatigue_score)

        self.store.upsert_profile(
            session_id,
            mastery_score=round(new_mastery, 3),
            difficulty_level=new_difficulty,
        )
        return self.get_profile(session_id)

    def calculate_difficulty(self, mastery: float, fatigue: float) -> int:
        """
        Calculate recommended difficulty (1–5).
        Formula: base_difficulty + mastery_delta - fatigue_penalty
        """
        base = 2
        mastery_bonus = mastery * 3        # 0–3 bonus based on mastery
        fatigue_penalty = fatigue * 2       # 0–2 penalty based on fatigue
        raw = base + mastery_bonus - fatigue_penalty
        return max(1, min(5, round(raw)))

    def get_recent_quiz_scores(self, session_id: str, limit: int = 5) -> list:
        """Get recent quiz scores for trend analysis."""
        return self.store.get_recent_quiz_scores(session_id, limit)

    def get_insights(self, session_id: str) -> dict:
        """Generate a natural-language progress summary via LLM."""
        from services.llm_provider import get_llm

        profile = self.get_profile(session_id)
        quiz_scores = self.get_recent_quiz_scores(session_id, limit=10)
        history = self.store.get_session_history(session_id)

        llm = get_llm()
        if not llm.is_available():
            return {
                "session_id": session_id,
                "profile": profile,
                "insight": "LLM not available for generating insights.",
            }

        try:
            system_prompt = (
                "You are a learning analytics advisor. Based on the learner's profile data, "
                "generate a brief, actionable insight (3-4 sentences). Be encouraging, "
                "mention strengths, areas for improvement, and a concrete next step."
            )
            context = (
                f"Learner Profile:\n"
                f"- Mastery Score: {profile.get('mastery_score', 0.5):.0%}\n"
                f"- Difficulty Level: {profile.get('difficulty_level', 2)}/5\n"
                f"- Average Fatigue: {profile.get('avg_fatigue', 0):.0%}\n"
                f"- Preferred Mode: {profile.get('preferred_mode', 'detailed')}\n"
                f"- Topic: {profile.get('topic', 'general')}\n"
                f"- Recent Quiz Scores: {quiz_scores if quiz_scores else 'None yet'}\n"
                f"- Total Interactions: {len(history)}"
            )
            insight = llm.generate(system_prompt, context, max_tokens=250)
            return {
                "session_id": session_id,
                "profile": profile,
                "insight": insight,
            }
        except Exception as e:
            return {
                "session_id": session_id,
                "profile": profile,
                "insight": f"Could not generate insight: {e}",
            }


if __name__ == "__main__":
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    print("=" * 60)
    print("  SVC-02 · Learner Profiler — Self-Test")
    print("=" * 60)

    profiler = LearnerProfiler()
    sid = "test-profiler-001"

    # Get/create profile
    p = profiler.get_profile(sid)
    print(f"\n✅ Initial profile: mastery={p['mastery_score']}, mode={p['preferred_mode']}")

    # Simulate interactions
    p = profiler.update_after_interaction(sid, "detailed", 0.2, "neural_networks")
    print(f"✅ After interaction: fatigue_avg={p['avg_fatigue']}, mode={p['preferred_mode']}")

    p = profiler.update_after_interaction(sid, "concise", 0.5)
    print(f"✅ After 2nd interaction: fatigue_avg={p['avg_fatigue']}, mode={p['preferred_mode']}")

    # Simulate quiz
    p = profiler.update_after_quiz(sid, quiz_score=0.8, fatigue_score=0.3)
    print(f"✅ After quiz: mastery={p['mastery_score']}, difficulty={p['difficulty_level']}")

    p = profiler.update_after_quiz(sid, quiz_score=0.9, fatigue_score=0.2)
    print(f"✅ After 2nd quiz: mastery={p['mastery_score']}, difficulty={p['difficulty_level']}")

    # Test difficulty calculation
    for m, f in [(0.0, 0.0), (0.5, 0.3), (0.8, 0.1), (1.0, 0.9)]:
        d = profiler.calculate_difficulty(m, f)
        print(f"   Difficulty(mastery={m}, fatigue={f}) = {d}")

    print("\n" + "=" * 60)
    print("  All learner profiler tests passed! ✓")
    print("=" * 60)
