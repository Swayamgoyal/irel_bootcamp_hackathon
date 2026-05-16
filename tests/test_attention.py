"""Unit tests for SVC-01 · Attention Monitor — FatigueClassifier."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.attention_monitor import FatigueClassifier, FatigueState


class TestFatigueClassifier:
    """Tests for the rule-based fatigue classifier."""

    def setup_method(self):
        self.classifier = FatigueClassifier()

    # ── Label classification tests ──────────────────────────────

    def test_fresh_classification(self):
        """Fast, consistent typing + quick response + good scores → FRESH."""
        result = self.classifier.classify(
            keypress_intervals=[120, 130, 125, 128, 122],
            response_delay_ms=2000,
            recent_quiz_scores=[0.9, 0.85, 0.95],
        )
        assert result.label == "FRESH"
        assert result.score < 0.25

    def test_moderate_classification(self):
        """Moderately slower typing + noticeable delay + declining quiz → MODERATE."""
        result = self.classifier.classify(
            keypress_intervals=[280, 350, 250, 400, 300, 450],
            response_delay_ms=12000,
            recent_quiz_scores=[0.9, 0.8, 0.65, 0.55],
        )
        assert result.label in ("MODERATE", "TIRED")  # boundary case
        assert 0.2 <= result.score <= 0.6

    def test_exhausted_classification(self):
        """Very slow, erratic typing + long delay + bad scores → EXHAUSTED."""
        result = self.classifier.classify(
            keypress_intervals=[600, 150, 900, 200, 1000, 300],
            response_delay_ms=28000,
            recent_quiz_scores=[0.8, 0.6, 0.3, 0.1],
        )
        assert result.label in ("TIRED", "EXHAUSTED")
        assert result.score >= 0.5

    # ── Score range tests ───────────────────────────────────────

    def test_score_always_in_range(self):
        """Score must always be 0.0-1.0."""
        test_cases = [
            ([50, 60, 55], 500, [1.0, 1.0]),
            ([2000, 3000, 5000], 60000, [0.0, 0.0, 0.0]),
            (None, None, None),
        ]
        for kp, delay, scores in test_cases:
            r = self.classifier.classify(kp, delay, scores)
            assert 0.0 <= r.score <= 1.0

    # ── Confidence tests ────────────────────────────────────────

    def test_full_confidence(self):
        """All 3 signals → confidence = 1.0."""
        result = self.classifier.classify([100, 120], 3000, [0.8, 0.7])
        assert result.confidence == 1.0

    def test_partial_confidence(self):
        """Only keypress → confidence = 0.33."""
        result = self.classifier.classify([100, 120], None, None)
        assert result.confidence == round(1 / 3, 2)

    def test_no_data_confidence(self):
        """No signals → confidence = 0.0."""
        result = self.classifier.classify()
        assert result.confidence == 0.0

    # ── Edge cases ──────────────────────────────────────────────

    def test_single_keypress(self):
        """Single keypress interval → keypress ignored (need ≥ 2)."""
        result = self.classifier.classify([100], 5000, [0.7, 0.6])
        assert result.signals["keypress_variance"] is None

    def test_single_quiz_score(self):
        """Single quiz score → quiz trend ignored (need ≥ 2)."""
        result = self.classifier.classify([100, 120], 3000, [0.8])
        assert result.signals["quiz_trend"] is None

    def test_zero_response_delay(self):
        """Zero delay → score 0 for delay signal."""
        result = self.classifier.classify(None, 0, None)
        assert result.signals["response_delay_norm"] == 0.0

    def test_to_dict(self):
        """FatigueState serialises correctly."""
        result = self.classifier.classify([100, 120], 5000, [0.8, 0.7])
        d = result.to_dict()
        assert "score" in d
        assert "label" in d
        assert "confidence" in d
        assert "signals" in d


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
