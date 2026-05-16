"""
SVC-05 · Orchestrator Agent
Port: 8000 | Central coordinator — the brain of the system

ReAct-style agentic loop: Observe -> Reason -> Act -> Reflect
Phase 1: Standalone script | Phase 2: FastAPI service
"""

import os
import uuid
import time
import json
from typing import Optional, List
from dotenv import load_dotenv

load_dotenv()

from services.attention_monitor import FatigueClassifier
from services.learner_profiler import LearnerProfiler
from services.content_adapter import ContentAdapter
from services.quiz_engine import QuizEngine
from services.data_store import DataStore
from services.llm_provider import get_llm


class Orchestrator:
    """Central coordinator implementing the ReAct agentic loop."""

    def __init__(self):
        self.data_store = DataStore()
        self.classifier = FatigueClassifier()
        self.profiler = LearnerProfiler(self.data_store)
        self.content_adapter = ContentAdapter()
        self.quiz_engine = QuizEngine()
        self.conversation_history: dict[str, list] = {}

    def interact(self, user_message: str, session_id: Optional[str] = None,
                 topic: Optional[str] = None,
                 keypress_intervals: Optional[List[float]] = None,
                 response_delay_ms: Optional[int] = None,
                 manual_mode: Optional[str] = None) -> dict:
        """Main entry point — full ReAct cycle."""
        if session_id is None:
            session_id = str(uuid.uuid4())[:8]
        self.data_store.create_session(session_id, topic=topic)
        effective_topic = topic or user_message

        # OBSERVE
        recent_scores = self.profiler.get_recent_quiz_scores(session_id)

        # REASON
        fatigue = self.classifier.classify(
            keypress_intervals=keypress_intervals,
            response_delay_ms=response_delay_ms,
            recent_quiz_scores=recent_scores if recent_scores else None,
        )
        profile = self.profiler.get_profile(session_id)
        mastery = profile.get("mastery_score", 0.5)
        difficulty = profile.get("difficulty_level", 2)
        mode = self.content_adapter.select_mode(fatigue.label, manual_mode)

        # ACT
        response_data = {}
        start_time = time.time()

        if mode == "quiz" and self.quiz_engine.llm.is_available():
            try:
                quiz = self.quiz_engine.generate_quiz(effective_topic, difficulty)
                response_data = {
                    "type": "quiz",
                    "content": self._format_quiz(quiz),
                    "quiz_data": quiz,
                    "mode_used": "quiz",
                }
            except Exception as e:
                mode = "concise"
                response_data = self._gen_safe(effective_topic, fatigue.label, mastery, difficulty, "concise")
        elif self.content_adapter.llm.is_available():
            response_data = self._gen_safe(effective_topic, fatigue.label, mastery, difficulty, mode)
        else:
            response_data = {
                "type": "content",
                "content": f"[No LLM] Would generate {mode} content for: {effective_topic}",
                "mode_used": mode,
            }

        elapsed = round(time.time() - start_time, 2)

        # REFLECT
        self.profiler.update_after_interaction(session_id, mode, fatigue.score, effective_topic)
        self.data_store.log_interaction(
            session_id=session_id, user_message=user_message, mode_used=mode,
            fatigue_score=fatigue.score, fatigue_label=fatigue.label,
            content_snippet=response_data.get("content", "")[:200],
        )
        if session_id not in self.conversation_history:
            self.conversation_history[session_id] = []
        self.conversation_history[session_id].append(
            {"user": user_message, "mode": mode, "fatigue": fatigue.label}
        )
        self.conversation_history[session_id] = self.conversation_history[session_id][-10:]

        return {
            "session_id": session_id,
            "content": response_data.get("content", ""),
            "mode_used": response_data.get("mode_used", mode),
            "fatigue_state": fatigue.to_dict(),
            "profile": self.profiler.get_profile(session_id),
            "response_time_seconds": elapsed,
            "type": response_data.get("type", "content"),
            "quiz_data": response_data.get("quiz_data"),
        }

    def submit_quiz_answer(self, session_id: str, question: str,
                           correct_answer: str, learner_answer: str,
                           topic: str = "") -> dict:
        if not self.quiz_engine.llm.is_available():
            return {"error": "No LLM configured"}
        eval_result = self.quiz_engine.evaluate_answer(question, correct_answer, learner_answer)
        self.data_store.store_quiz_result(
            session_id=session_id, topic=topic, question=question,
            correct_answer=correct_answer, learner_answer=learner_answer,
            score=eval_result["score"], feedback=eval_result["feedback"],
        )
        profile = self.profiler.update_after_quiz(session_id, eval_result["score"])
        return {"evaluation": eval_result, "updated_profile": profile}

    def get_session_summary(self, session_id: str) -> dict:
        history = self.data_store.get_session_history(session_id)
        profile = self.profiler.get_profile(session_id)
        quizzes = self.data_store.get_quiz_history(session_id)
        modes = {}
        for h in history:
            m = h.get("mode_used", "unknown")
            modes[m] = modes.get(m, 0) + 1

        stats = {
            "session_id": session_id,
            "total_interactions": len(history),
            "total_quizzes": len(quizzes),
            "profile": profile,
            "mode_distribution": modes,
            "avg_fatigue": profile.get("avg_fatigue", 0),
        }

        # Generate LLM-powered narrative summary
        llm = get_llm()
        if llm.is_available() and history:
            try:
                topics_covered = list(set(
                    h.get("user_message", "")[:60] for h in history if h.get("user_message")
                ))
                quiz_scores = [q.get("score", 0) for q in quizzes if q.get("score") is not None]
                avg_quiz = sum(quiz_scores) / len(quiz_scores) if quiz_scores else None

                summary_prompt = (
                    "You are a learning analytics assistant. Generate a brief, encouraging "
                    "session recap (3-5 sentences) for a student. Be warm and specific.\n"
                    "Include: topics covered, learning progress, fatigue patterns, and a suggestion for next time."
                )
                context = (
                    f"Session stats:\n"
                    f"- Total interactions: {len(history)}\n"
                    f"- Topics explored: {', '.join(topics_covered[:5])}\n"
                    f"- Modes used: {modes}\n"
                    f"- Average fatigue: {profile.get('avg_fatigue', 0):.0%}\n"
                    f"- Mastery score: {profile.get('mastery_score', 0.5):.0%}\n"
                    f"- Quizzes taken: {len(quizzes)}"
                    + (f", avg score: {avg_quiz:.0%}" if avg_quiz else "")
                )
                narrative = llm.generate(summary_prompt, context, max_tokens=300)
                stats["narrative_summary"] = narrative
            except Exception:
                stats["narrative_summary"] = None
        else:
            stats["narrative_summary"] = None

        return stats

    def _gen_safe(self, topic, fatigue_label, mastery, difficulty, mode):
        try:
            result = self.content_adapter.generate_content(
                topic=topic, fatigue_label=fatigue_label,
                mastery_level=max(1, min(5, round(mastery * 5))),
                difficulty=difficulty, manual_mode=mode,
            )
            return {"type": "content", **result}
        except Exception as e:
            return {"type": "content", "content": f"[Error: {e}]", "mode_used": mode}

    def _format_quiz(self, quiz: dict) -> str:
        lines = [f"**{quiz['question']}**\n"]
        if quiz.get("options"):
            for opt in quiz["options"]:
                lines.append(f"- {opt}")
            lines.append("")
        lines.append("*Type your answer below.*")
        return "\n".join(lines)


# ─── CLI Interactive Runner ───────────────────────────────────────────
if __name__ == "__main__":
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8", errors="replace")
    print("=" * 60)
    print("  Attention-Aware Study Assistant — Terminal Mode")
    print("=" * 60)

    orch = Orchestrator()
    session_id = str(uuid.uuid4())[:8]
    print(f"\nSession: {session_id} | LLM: {orch.content_adapter.llm.get_info()}")
    print("Commands: /quiz <topic>, /summary, /quit\n")

    fatigue_sim = [
        (None, None), ([150,140,160,130], 2500), ([200,250,180,300], 6000),
        ([350,200,500,280], 12000), ([600,150,800,200], 22000),
    ]
    n = 0

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not user_input:
            continue
        if user_input.lower() == "/quit":
            break
        if user_input.lower() == "/summary":
            print(json.dumps(orch.get_session_summary(session_id), indent=2, default=str))
            continue

        idx = min(n, len(fatigue_sim) - 1)
        kp, delay = fatigue_sim[idx]
        is_quiz = user_input.lower().startswith("/quiz")
        topic = user_input.replace("/quiz", "").strip() or "general knowledge"

        result = orch.interact(
            user_message=topic if is_quiz else user_input,
            session_id=session_id,
            keypress_intervals=kp, response_delay_ms=delay,
            manual_mode="quiz" if is_quiz else None,
        )

        fs = result["fatigue_state"]
        print(f"\n[{result['mode_used'].upper()}] Fatigue: {fs['label']} ({fs['score']})")
        print("-" * 40)
        print(result["content"])

        if result.get("type") == "quiz" and result.get("quiz_data"):
            try:
                answer = input("\nYour answer: ").strip()
                if answer:
                    qd = result["quiz_data"]
                    ev = orch.submit_quiz_answer(session_id, qd["question"], qd["correct_answer"], answer, topic)
                    e = ev["evaluation"]
                    print(f"\nScore: {e['score']} | Correct: {e['is_correct']}")
                    print(f"Feedback: {e['feedback']}")
            except (EOFError, KeyboardInterrupt):
                pass
        n += 1

    s = orch.get_session_summary(session_id)
    print(f"\nSession done! {s['total_interactions']} interactions, {s['total_quizzes']} quizzes")
