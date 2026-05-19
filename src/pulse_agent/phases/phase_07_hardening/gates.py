from __future__ import annotations

import logging
import os

from pulse_agent.config.loader import AppConfig

logger = logging.getLogger(__name__)

NON_PRODUCTION_ENVS = frozenset({"dev", "development", "local", "staging", "test"})


class ProductionGateError(RuntimeError):
    pass


def effective_email_mode(config: AppConfig) -> str:
    """
    Staging/dev always draft. Production send requires PULSE_PRODUCTION_SEND_APPROVED=true.
    """
    requested = os.environ.get("EMAIL_MODE", config.email_mode or "draft").strip().lower()
    if requested not in ("draft", "send"):
        raise ValueError(f"EMAIL_MODE must be 'draft' or 'send', got {requested!r}")

    env = (config.pulse_env or "dev").strip().lower()
    if env in NON_PRODUCTION_ENVS:
        if requested == "send":
            logger.warning(
                "EMAIL_MODE=send ignored in PULSE_ENV=%s; using draft", env
            )
        return "draft"

    if requested == "send":
        approved = os.environ.get("PULSE_PRODUCTION_SEND_APPROVED", "").strip().lower()
        if approved not in ("true", "1", "yes"):
            raise ProductionGateError(
                "EMAIL_MODE=send in production requires "
                "PULSE_PRODUCTION_SEND_APPROVED=true and completed "
                "docs/production-send-checklist.md"
            )
    return requested
