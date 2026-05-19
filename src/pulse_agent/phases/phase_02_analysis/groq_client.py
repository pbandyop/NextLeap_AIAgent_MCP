from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Protocol

import httpx

from pulse_agent.phases.phase_02_analysis.config import AnalysisLimits, GroqSettings
from pulse_agent.phases.phase_02_analysis.parser import LlmParseError, parse_theme_response
from pulse_agent.phases.phase_02_analysis.prompts import SYSTEM_PROMPT
from pulse_agent.phases.phase_02_analysis.sampling import estimate_tokens

logger = logging.getLogger(__name__)


@dataclass
class GroqUsage:
    requests: int = 0
    tokens_estimated: int = 0

    def can_call(self, limits: AnalysisLimits, extra_tokens: int = 0) -> bool:
        if self.requests >= limits.max_groq_requests_per_run:
            return False
        if self.tokens_estimated + extra_tokens > limits.max_tokens_per_run:
            return False
        return True

    def record(self, tokens: int) -> None:
        self.requests += 1
        self.tokens_estimated += tokens


class ThemeLlmClient(Protocol):
    def complete_theme(self, user_prompt: str) -> dict: ...


@dataclass
class StubThemeLlmClient:
    """Deterministic themes for tests and dry-run without API key."""

    usage: GroqUsage = field(default_factory=GroqUsage)

    def complete_theme(self, user_prompt: str) -> dict:
        first_line = ""
        for line in user_prompt.splitlines():
            if line.strip().startswith("1."):
                first_line = line.split(":", 1)[-1].strip()[:80]
                break
        label = "User feedback theme"
        if "login" in user_prompt.lower():
            label = "Login and access issues"
        elif "charge" in user_prompt.lower() or "fee" in user_prompt.lower():
            label = "Fees and charges"
        elif "great" in user_prompt.lower() or "good" in user_prompt.lower():
            label = "Positive product experience"
        tokens = estimate_tokens(user_prompt) + 80
        self.usage.record(tokens)
        return {
            "label": label,
            "summary": f"Users discuss: {first_line or 'app experience'}.",
            "actions": ["Monitor trend weekly", "Validate with support tickets"],
        }


@dataclass
class GroqThemeClient:
    settings: GroqSettings
    limits: AnalysisLimits
    usage: GroqUsage = field(default_factory=GroqUsage)
    _last_call_at: float = 0.0

    def complete_theme(self, user_prompt: str) -> dict:
        est = estimate_tokens(SYSTEM_PROMPT) + estimate_tokens(user_prompt) + 150
        if not self.usage.can_call(self.limits, est):
            raise RuntimeError("Groq per-run budget exhausted")

        self._throttle()
        payload = {
            "model": self.settings.model,
            "temperature": self.limits.groq_temperature,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": f"Bearer {self.settings.api_key}",
            "Content-Type": "application/json",
        }
        url = f"{self.settings.base_url}/chat/completions"

        last_exc: Exception | None = None
        for attempt, delay in enumerate([0, 2, 4, 8]):
            if delay:
                time.sleep(delay)
            try:
                with httpx.Client(timeout=60.0) as client:
                    response = client.post(url, json=payload, headers=headers)
                if response.status_code == 429:
                    last_exc = RuntimeError("Groq rate limit (429)")
                    continue
                response.raise_for_status()
                body = response.json()
                content = body["choices"][0]["message"]["content"]
                usage = body.get("usage") or {}
                total_tokens = int(
                    usage.get("total_tokens")
                    or (estimate_tokens(content) + est)
                )
                self.usage.record(total_tokens)
                return parse_theme_response(content)
            except (httpx.HTTPError, LlmParseError, KeyError) as exc:
                last_exc = exc
                logger.warning("Groq call failed (attempt %s): %s", attempt + 1, exc)

        raise RuntimeError(f"Groq call failed after retries: {last_exc}") from last_exc

    def _throttle(self) -> None:
        delay_s = self.limits.inter_request_delay_ms / 1000.0
        elapsed = time.time() - self._last_call_at
        if self._last_call_at and elapsed < delay_s:
            time.sleep(delay_s - elapsed)
        self._last_call_at = time.time()


def build_theme_client(
    settings: GroqSettings,
    limits: AnalysisLimits,
    *,
    force_stub: bool = False,
) -> ThemeLlmClient:
    if force_stub or not settings.api_key:
        return StubThemeLlmClient()
    return GroqThemeClient(settings=settings, limits=limits)
