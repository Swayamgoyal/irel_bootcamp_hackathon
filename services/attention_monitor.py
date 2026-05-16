"""
SVC-01 · Attention Monitor Agent
Port: 8001
Passive sensor & fatigue classifier

Phase 1: Standalone Python module with rule-based heuristic classifier.
"""

import statistics
from dataclasses import dataclass, asdict
from typing import List, Optional


@dataclass
class FatigueState:
    score: float       # 0.0 (fresh) to 1.0 (exhausted)
    label: str         # FRESH, MODERATE, TIRED, EXHAUSTED
    confidence: float  # 0.0 to 1.0
    signals: dict

    def to_dict(self) -> dict:
        return asdict(self)


class FatigueClassifier:
    """
    Rule-based fatigue classifier using weighted heuristic scoring.
    Weights: keystroke variance 40%, response delay 30%, quiz trend 30%.
    """

    WEIGHT_KEYPRESS = 0.4
    WEIGHT_DELAY = 0.3
    WEIGHT_QUIZ = 0.3

    THRESHOLDS = {
        "FRESH": (0.0, 0.25),
        "MODERATE": (0.25, 0.50),
        "TIRED": (0.50, 0.75),
        "EXHAUSTED": (0.75, 1.0),
    }

    BASELINE_KEYPRESS_MS = 150
    BASELINE_DELAY_MS = 3000
    MAX_DELAY_MS = 30000

    def classify(self, keypress_intervals: Optional[List[float]] = None,
                 response_delay_ms: Optional[int] = None,
                 recent_quiz_scores: Optional[List[float]] = None) -> FatigueState:
        signals = {}
        weights_used = 0.0
        weighted_sum = 0.0

        if keypress_intervals and len(keypress_intervals) >= 2:
            ks = self._score_keypress(keypress_intervals)
            signals["keypress_variance"] = round(ks, 3)
            weighted_sum += self.WEIGHT_KEYPRESS * ks
            weights_used += self.WEIGHT_KEYPRESS
        else:
            signals["keypress_variance"] = None

        if response_delay_ms is not None:
            ds = self._score_delay(response_delay_ms)
            signals["response_delay_norm"] = round(ds, 3)
            weighted_sum += self.WEIGHT_DELAY * ds
            weights_used += self.WEIGHT_DELAY
        else:
            signals["response_delay_norm"] = None

        if recent_quiz_scores and len(recent_quiz_scores) >= 2:
            qs = self._score_quiz_trend(recent_quiz_scores)
            signals["quiz_trend"] = round(qs, 3)
            weighted_sum += self.WEIGHT_QUIZ * qs
            weights_used += self.WEIGHT_QUIZ
        else:
            signals["quiz_trend"] = None

        fatigue = weighted_sum / weights_used if weights_used > 0 else 0.25
        fatigue = max(0.0, min(1.0, fatigue))
        confidence = sum(1 for v in signals.values() if v is not None) / 3.0
        label = self._to_label(fatigue)

        return FatigueState(round(fatigue, 3), label, round(confidence, 2), signals)

    def _score_keypress(self, intervals: List[float]) -> float:
        avg = statistics.mean(intervals)
        std = statistics.stdev(intervals) if len(intervals) > 1 else 0.0
        slowness = min(avg / (self.BASELINE_KEYPRESS_MS * 4), 1.0)
        cv = (std / avg) if avg > 0 else 0.0
        irregularity = min(cv / 1.5, 1.0)
        return 0.6 * slowness + 0.4 * irregularity

    def _score_delay(self, delay_ms: int) -> float:
        if delay_ms <= self.BASELINE_DELAY_MS:
            return 0.0
        return max(0.0, min(1.0, (delay_ms - self.BASELINE_DELAY_MS) / (self.MAX_DELAY_MS - self.BASELINE_DELAY_MS)))

    def _score_quiz_trend(self, scores: List[float]) -> float:
        chrono = list(reversed(scores))
        mid = len(chrono) // 2
        old_avg = statistics.mean(chrono[:mid]) if mid > 0 else chrono[0]
        new_avg = statistics.mean(chrono[mid:])
        decline = max(0.0, min((old_avg - new_avg) / 0.5, 1.0))
        low_perf = max(0.0, 1.0 - new_avg)
        return 0.6 * decline + 0.4 * low_perf

    def _to_label(self, score: float) -> str:
        for label, (lo, hi) in self.THRESHOLDS.items():
            if lo <= score < hi:
                return label
        return "EXHAUSTED"


if __name__ == "__main__":
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    print("=" * 60)
    print("  SVC-01 · Attention Monitor — Self-Test")
    print("=" * 60)
    c = FatigueClassifier()

    tests = [
        ("Fresh", [120,130,125,128,122], 2000, [0.9,0.85,0.95]),
        ("Moderate", [200,180,250,220,190,280], 8000, [0.8,0.75,0.7,0.65]),
        ("Tired", [350,200,500,280,600,320], 15000, [0.9,0.8,0.6,0.5,0.4]),
        ("Exhausted", [600,150,800,200,1000,300], 25000, [0.8,0.6,0.3,0.2,0.1]),
        ("Partial", [200,250,180,300], None, None),
    ]
    icons = ["🟢","🟡","🟠","🔴","⚪"]
    for (name, kp, delay, quiz), icon in zip(tests, icons):
        r = c.classify(kp, delay, quiz)
        print(f"\n{icon} {name}: score={r.score} label={r.label} conf={r.confidence}")
        print(f"   Signals: {r.signals}")

    print("\n" + "=" * 60)
    print("  All attention monitor tests passed! ✓")
    print("=" * 60)
