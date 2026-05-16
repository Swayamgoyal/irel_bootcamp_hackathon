"""
SVC-03 · Content Adaptation Agent
Port: 8003 | Dynamic content generator & mode switcher

Uses the unified LLM provider (Gemini / Ollama / Anthropic) with
Jinja2 prompt templates for 4 adaptive teaching modes.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader
from services.llm_provider import get_llm

load_dotenv()

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

MODE_MAP = {
    "FRESH": "detailed",
    "MODERATE": "concise",
    "TIRED": "analogy",
    "EXHAUSTED": "quiz",
}


class ContentAdapter:
    """Generates adaptive content using LLM with mode-specific Jinja2 prompts."""

    def __init__(self):
        self.llm = get_llm()
        self.jinja_env = Environment(loader=FileSystemLoader(str(PROMPTS_DIR)))

    def select_mode(self, fatigue_label: str, manual_override: Optional[str] = None) -> str:
        if manual_override and manual_override in ("concise", "detailed", "analogy", "quiz"):
            return manual_override
        return MODE_MAP.get(fatigue_label, "detailed")

    def render_prompt(self, mode: str, topic: str,
                      mastery_level: int = 2, difficulty: int = 2) -> str:
        template = self.jinja_env.get_template(f"{mode}.j2")
        return template.render(topic=topic, mastery_level=mastery_level, difficulty=difficulty)

    def generate_content(self, topic: str, fatigue_label: str = "FRESH",
                         mastery_level: int = 2, difficulty: int = 2,
                         manual_mode: Optional[str] = None) -> dict:
        mode = self.select_mode(fatigue_label, manual_mode)
        system_prompt = self.render_prompt(mode, topic, mastery_level, difficulty)

        content = self.llm.generate(system_prompt, f"Teach me about: {topic}")

        word_count = len(content.split())
        read_seconds = max(10, int(word_count / 200 * 60))

        return {
            "content": content,
            "mode_used": mode,
            "estimated_read_seconds": read_seconds,
            "difficulty_level": difficulty,
            "word_count": word_count,
        }


if __name__ == "__main__":
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    print("=" * 60)
    print("  SVC-03 · Content Adapter — Self-Test")
    print("=" * 60)

    adapter = ContentAdapter()
    print(f"\nLLM: {adapter.llm.get_info()}")

    # Test template rendering
    for mode in ["concise", "detailed", "analogy", "quiz"]:
        prompt = adapter.render_prompt(mode, "Neural Networks", 3, 3)
        print(f"\n📝 {mode.upper()} template ({len(prompt)} chars): {prompt[:80]}...")

    if adapter.llm.is_available():
        print("\n--- Live API test ---")
        result = adapter.generate_content("What is gradient descent?", "FRESH", 3, 3)
        print(f"Mode: {result['mode_used']} | Words: {result['word_count']}")
        print(result["content"][:300] + "...")
    else:
        print("\n⚠️  No LLM configured. Templates verified OK.")

    print("\n" + "=" * 60)
    print("  Content adapter tests complete! ✓")
    print("=" * 60)
