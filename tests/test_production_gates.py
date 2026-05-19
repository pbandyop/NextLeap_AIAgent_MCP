import os

import pytest

from pulse_agent.config.loader import AppConfig, ProductConfig
from pulse_agent.phases.phase_07_hardening.gates import (
    ProductionGateError,
    effective_email_mode,
)


def test_staging_forces_draft(monkeypatch):
    monkeypatch.setenv("PULSE_ENV", "staging")
    monkeypatch.setenv("EMAIL_MODE", "send")
    config = AppConfig(
        products={},
        mcp_servers={},
        pulse_env="staging",
        email_mode="send",
    )
    assert effective_email_mode(config) == "draft"


def test_production_send_requires_approval(monkeypatch):
    monkeypatch.setenv("PULSE_ENV", "production")
    monkeypatch.setenv("EMAIL_MODE", "send")
    monkeypatch.delenv("PULSE_PRODUCTION_SEND_APPROVED", raising=False)
    config = AppConfig(products={}, mcp_servers={}, pulse_env="production")
    with pytest.raises(ProductionGateError):
        effective_email_mode(config)
