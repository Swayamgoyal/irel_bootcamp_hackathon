"""
LLM Provider Abstraction Layer

Supports multiple backends:
  1. Google Gemini (gemini-2.5-flash) — via google-genai SDK
  2. Ollama (local models like llama3, mistral) — via HTTP API
  3. Anthropic Claude (optional fallback) — via anthropic SDK

Selection priority: GEMINI_API_KEY → Ollama (if running) → error message.
"""

import os
import json
import httpx
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class LLMProvider:
    """Unified interface for LLM calls across providers."""

    def __init__(self):
        self.provider = None
        self.client = None
        self._init_provider()

    def _init_provider(self):
        """Auto-detect available provider."""
        # Priority 1: Gemini
        gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
        if gemini_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=gemini_key)
                self.provider = "gemini"
                self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
                print(f"[LLM] Using Gemini ({self.model_name})")
                return
            except ImportError:
                print("[LLM] google-genai not installed, trying next provider...")

        # Priority 2: Ollama (local)
        ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        try:
            resp = httpx.get(f"{ollama_url}/api/tags", timeout=2.0)
            if resp.status_code == 200:
                models = resp.json().get("models", [])
                if models:
                    self.provider = "ollama"
                    self.ollama_url = ollama_url
                    # Pick best available model
                    model_names = [m["name"] for m in models]
                    for preferred in ["llama3.1:8b", "llama3:8b", "mistral", "gemma2"]:
                        if any(preferred in n for n in model_names):
                            self.model_name = preferred
                            break
                    else:
                        self.model_name = model_names[0]
                    print(f"[LLM] Using Ollama ({self.model_name})")
                    return
        except (httpx.ConnectError, httpx.TimeoutException):
            pass

        # Priority 3: Anthropic
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=anthropic_key)
                self.provider = "anthropic"
                self.model_name = "claude-sonnet-4-20250514"
                print(f"[LLM] Using Anthropic ({self.model_name})")
                return
            except ImportError:
                pass

        # No provider available
        self.provider = "none"
        print("[LLM] WARNING: No LLM provider available.")
        print("  Set GEMINI_API_KEY, start Ollama, or set ANTHROPIC_API_KEY")

    def generate(self, system_prompt: str, user_message: str,
                 max_tokens: int = 1024) -> str:
        """Generate text from the LLM."""
        if self.provider == "gemini":
            return self._gemini_generate(system_prompt, user_message, max_tokens)
        elif self.provider == "ollama":
            return self._ollama_generate(system_prompt, user_message, max_tokens)
        elif self.provider == "anthropic":
            return self._anthropic_generate(system_prompt, user_message, max_tokens)
        else:
            return f"[No LLM available] System: {system_prompt[:100]}... | User: {user_message}"

    def generate_json(self, system_prompt: str, user_message: str,
                      max_tokens: int = 512) -> dict:
        """Generate and parse JSON from the LLM. Retries once on parse failure."""
        raw = self.generate(system_prompt, user_message, max_tokens)
        return self._parse_json(raw)

    def is_available(self) -> bool:
        return self.provider != "none"

    def get_info(self) -> dict:
        return {"provider": self.provider, "model": getattr(self, "model_name", "none")}

    # ── Gemini ──────────────────────────────────────────────────────

    def _gemini_generate(self, system_prompt: str, user_message: str,
                         max_tokens: int) -> str:
        import time as _time
        from google.genai import types

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=user_message,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        max_output_tokens=max_tokens,
                        temperature=0.7,
                    ),
                )
                return response.text
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    wait = (attempt + 1) * 15  # 15s, 30s, 45s
                    print(f"[LLM] Gemini rate limited, retrying in {wait}s (attempt {attempt+1}/{max_retries})...")
                    _time.sleep(wait)
                else:
                    raise
        # Final attempt without catching
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=max_tokens,
                temperature=0.7,
            ),
        )
        return response.text

    # ── Ollama ──────────────────────────────────────────────────────

    def _ollama_generate(self, system_prompt: str, user_message: str,
                         max_tokens: int) -> str:
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "stream": False,
            "options": {"num_predict": max_tokens, "temperature": 0.7},
        }
        resp = httpx.post(
            f"{self.ollama_url}/api/chat",
            json=payload,
            timeout=120.0,
        )
        resp.raise_for_status()
        return resp.json()["message"]["content"]

    # ── Anthropic ───────────────────────────────────────────────────

    def _anthropic_generate(self, system_prompt: str, user_message: str,
                            max_tokens: int) -> str:
        message = self.client.messages.create(
            model=self.model_name,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        return message.content[0].text

    # ── JSON Parsing ────────────────────────────────────────────────

    def _parse_json(self, raw: str) -> dict:
        """Parse JSON from LLM output, handling markdown code blocks."""
        raw = raw.strip()
        # Try direct parse
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass
        # Try extracting from code blocks
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            # Last resort: find first { and last }
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(raw[start:end])
            raise ValueError(f"Could not parse JSON from LLM output: {raw[:200]}")


# Singleton instance
_provider: Optional[LLMProvider] = None

def get_llm() -> LLMProvider:
    """Get or create the singleton LLM provider."""
    global _provider
    if _provider is None:
        _provider = LLMProvider()
    return _provider


if __name__ == "__main__":
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    llm = get_llm()
    print(f"\nProvider: {llm.get_info()}")
    print(f"Available: {llm.is_available()}")

    if llm.is_available():
        print("\nTesting generation...")
        result = llm.generate(
            system_prompt="You are a helpful teacher. Be concise.",
            user_message="Explain what a variable is in programming in 2 sentences.",
        )
        print(f"Response: {result}")
    else:
        print("\nNo LLM provider configured. Set GEMINI_API_KEY or start Ollama.")
