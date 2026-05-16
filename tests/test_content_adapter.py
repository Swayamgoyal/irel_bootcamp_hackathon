"""Unit tests for SVC-03 · Content Adaptation Agent — mode selection & templates."""

import sys
import os
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.content_adapter import ContentAdapter, MODE_MAP


class TestModeSelection:
    """Tests for fatigue-to-mode mapping and manual override."""

    def setup_method(self):
        self.adapter = ContentAdapter()

    def test_fresh_maps_to_detailed(self):
        assert self.adapter.select_mode("FRESH") == "detailed"

    def test_moderate_maps_to_concise(self):
        assert self.adapter.select_mode("MODERATE") == "concise"

    def test_tired_maps_to_analogy(self):
        assert self.adapter.select_mode("TIRED") == "analogy"

    def test_exhausted_maps_to_quiz(self):
        assert self.adapter.select_mode("EXHAUSTED") == "quiz"

    def test_unknown_label_defaults_to_detailed(self):
        assert self.adapter.select_mode("UNKNOWN") == "detailed"

    def test_manual_override_concise(self):
        assert self.adapter.select_mode("FRESH", manual_override="concise") == "concise"

    def test_manual_override_quiz(self):
        assert self.adapter.select_mode("FRESH", manual_override="quiz") == "quiz"

    def test_invalid_manual_override_ignored(self):
        """Invalid manual mode should fall back to fatigue-based selection."""
        assert self.adapter.select_mode("FRESH", manual_override="invalid") == "detailed"


class TestPromptRendering:
    """Tests for Jinja2 template rendering."""

    def setup_method(self):
        self.adapter = ContentAdapter()

    def test_concise_template_renders(self):
        prompt = self.adapter.render_prompt("concise", "Machine Learning")
        assert "Machine Learning" in prompt
        assert len(prompt) > 50

    def test_detailed_template_renders(self):
        prompt = self.adapter.render_prompt("detailed", "Neural Networks")
        assert "Neural Networks" in prompt

    def test_analogy_template_renders(self):
        prompt = self.adapter.render_prompt("analogy", "Databases")
        assert "Databases" in prompt

    def test_quiz_template_renders(self):
        prompt = self.adapter.render_prompt("quiz", "Sorting Algorithms")
        assert "Sorting Algorithms" in prompt

    def test_mastery_level_injected(self):
        prompt = self.adapter.render_prompt("detailed", "Test", mastery_level=4)
        assert "4" in prompt

    def test_difficulty_injected(self):
        prompt = self.adapter.render_prompt("concise", "Test", difficulty=5)
        assert "5" in prompt


class TestContentGeneration:
    """Tests for the generate_content output structure."""

    def setup_method(self):
        self.adapter = ContentAdapter()

    @pytest.mark.skipif(
        not ContentAdapter().llm.is_available(),
        reason="No LLM provider available",
    )
    def test_generate_returns_required_keys(self):
        result = self.adapter.generate_content("Variables in Python", "FRESH")
        assert "content" in result
        assert "mode_used" in result
        assert "estimated_read_seconds" in result
        assert "difficulty_level" in result
        assert "word_count" in result

    @pytest.mark.skipif(
        not ContentAdapter().llm.is_available(),
        reason="No LLM provider available",
    )
    def test_generate_mode_matches_fatigue(self):
        result = self.adapter.generate_content("Loops", "TIRED")
        assert result["mode_used"] == "analogy"

    @pytest.mark.skipif(
        not ContentAdapter().llm.is_available(),
        reason="No LLM provider available",
    )
    def test_read_time_positive(self):
        result = self.adapter.generate_content("Arrays", "FRESH")
        assert result["estimated_read_seconds"] >= 10

    @pytest.mark.skipif(
        not ContentAdapter().llm.is_available(),
        reason="No LLM provider available",
    )
    def test_word_count_positive(self):
        result = self.adapter.generate_content("Functions", "MODERATE")
        assert result["word_count"] > 0


class TestModeMap:
    """Tests for the MODE_MAP constant."""

    def test_all_fatigue_labels_mapped(self):
        for label in ["FRESH", "MODERATE", "TIRED", "EXHAUSTED"]:
            assert label in MODE_MAP

    def test_all_modes_present(self):
        modes = set(MODE_MAP.values())
        assert modes == {"detailed", "concise", "analogy", "quiz"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
