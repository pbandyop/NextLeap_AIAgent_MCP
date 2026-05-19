from pulse_agent.safety.pii import REDACT_EMAIL, REDACT_PHONE, scrub_pii


def test_scrub_email():
    text = "Contact me at user.name@example.com for help"
    out = scrub_pii(text)
    assert "user.name@example.com" not in out
    assert REDACT_EMAIL in out


def test_scrub_phone_india():
    text = "Call me on +91 9876543210 anytime"
    out = scrub_pii(text)
    assert "9876543210" not in out
    assert REDACT_PHONE in out


def test_scrub_preserves_normal_review():
    text = "Great app but login is slow"
    assert scrub_pii(text) == text
