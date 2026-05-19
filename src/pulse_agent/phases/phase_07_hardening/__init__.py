"""Phase 7 — Hardening: PII, production gates, run metrics."""

from pulse_agent.phases.phase_07_hardening.gates import ProductionGateError, effective_email_mode

__all__ = ["effective_email_mode", "ProductionGateError"]
