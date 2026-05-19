from __future__ import annotations

from pulse_agent.models.render import RenderedDelivery
from pulse_agent.models.review import Review
from pulse_agent.safety.injection import sanitize_review_text
from pulse_agent.safety.pii import scrub_pii


def scrub_review_fields(review: Review) -> Review:
    return Review(
        source=review.source,
        review_id=review.review_id,
        rating=review.rating,
        title=scrub_pii(sanitize_review_text(review.title)),
        body=scrub_pii(sanitize_review_text(review.body)),
        review_date=review.review_date,
        author=scrub_pii(review.author) if review.author else None,
        locale=review.locale,
        app_version=review.app_version,
    )


def scrub_corpus_reviews(reviews: list[Review]) -> list[Review]:
    return [scrub_review_fields(r) for r in reviews]


def scrub_rendered_for_publish(rendered: RenderedDelivery) -> RenderedDelivery:
    from pulse_agent.models.render import DocSectionPayload, EmailTeaserPayload

    return RenderedDelivery(
        doc_section=DocSectionPayload(
            heading=rendered.doc_section.heading,
            anchor=rendered.doc_section.anchor,
            content=scrub_pii(rendered.doc_section.content),
        ),
        email_teaser=EmailTeaserPayload(
            subject=rendered.email_teaser.subject,
            body_plain=scrub_pii(rendered.email_teaser.body_plain),
            body_html=scrub_pii(rendered.email_teaser.body_html),
            doc_link_placeholder=rendered.email_teaser.doc_link_placeholder,
            to_recipients=list(rendered.email_teaser.to_recipients),
        ),
        review_count=rendered.review_count,
        theme_count=rendered.theme_count,
    )
