from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DocSectionPayload:
    heading: str
    anchor: str
    content: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "heading": self.heading,
            "anchor": self.anchor,
            "content": self.content,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DocSectionPayload:
        return cls(
            heading=str(data["heading"]),
            anchor=str(data["anchor"]),
            content=str(data["content"]),
        )


@dataclass
class EmailTeaserPayload:
    subject: str
    body_plain: str
    body_html: str
    doc_link_placeholder: str
    to_recipients: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject": self.subject,
            "body_plain": self.body_plain,
            "body_html": self.body_html,
            "doc_link_placeholder": self.doc_link_placeholder,
            "to_recipients": list(self.to_recipients),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EmailTeaserPayload:
        return cls(
            subject=str(data["subject"]),
            body_plain=str(data["body_plain"]),
            body_html=str(data["body_html"]),
            doc_link_placeholder=str(data.get("doc_link_placeholder", "{{DOC_LINK}}")),
            to_recipients=list(data.get("to_recipients") or []),
        )


@dataclass
class RenderedDelivery:
    doc_section: DocSectionPayload
    email_teaser: EmailTeaserPayload
    review_count: int = 0
    theme_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "doc_section": self.doc_section.to_dict(),
            "email_teaser": self.email_teaser.to_dict(),
            "review_count": self.review_count,
            "theme_count": self.theme_count,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RenderedDelivery:
        return cls(
            doc_section=DocSectionPayload.from_dict(data["doc_section"]),
            email_teaser=EmailTeaserPayload.from_dict(data["email_teaser"]),
            review_count=int(data.get("review_count", 0)),
            theme_count=int(data.get("theme_count", 0)),
        )
