from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class DocsDeliveryResult:
    doc_id: str
    section_heading: str
    section_url: str
    anchor: str
    idempotency_key: str
    status: str  # success | skipped | error
    message: str = ""
    document_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "section_heading": self.section_heading,
            "section_url": self.section_url,
            "anchor": self.anchor,
            "idempotency_key": self.idempotency_key,
            "status": self.status,
            "message": self.message,
            "document_id": self.document_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DocsDeliveryResult:
        return cls(
            doc_id=str(data["doc_id"]),
            section_heading=str(data["section_heading"]),
            section_url=str(data["section_url"]),
            anchor=str(data.get("anchor", "")),
            idempotency_key=str(data.get("idempotency_key", "")),
            status=str(data.get("status", "success")),
            message=str(data.get("message", "")),
            document_id=data.get("document_id"),
        )


@dataclass
class GmailDeliveryResult:
    to: str
    subject: str
    mode: str  # draft | send
    idempotency_key: str
    section_url: str
    status: str  # success | skipped | error
    gmail_message_id: str | None = None
    gmail_draft_id: str | None = None
    message: str = ""
    run_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "to": self.to,
            "subject": self.subject,
            "mode": self.mode,
            "idempotency_key": self.idempotency_key,
            "section_url": self.section_url,
            "status": self.status,
            "gmail_message_id": self.gmail_message_id,
            "gmail_draft_id": self.gmail_draft_id,
            "message": self.message,
            "run_id": self.run_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GmailDeliveryResult:
        return cls(
            to=str(data["to"]),
            subject=str(data["subject"]),
            mode=str(data.get("mode", "draft")),
            idempotency_key=str(data.get("idempotency_key", "")),
            section_url=str(data.get("section_url", "")),
            status=str(data.get("status", "success")),
            gmail_message_id=data.get("gmail_message_id"),
            gmail_draft_id=data.get("gmail_draft_id"),
            message=str(data.get("message", "")),
            run_id=str(data.get("run_id", "")),
        )
