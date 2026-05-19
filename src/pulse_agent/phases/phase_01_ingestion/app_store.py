from __future__ import annotations

import json
import logging
import xml.etree.ElementTree as ET
from datetime import date, datetime
from typing import Any

import httpx

from pulse_agent.models.review import Review, ReviewSource

logger = logging.getLogger(__name__)

ITUNES_RSS_JSON = (
    "https://itunes.apple.com/{country}/rss/customerreviews"
    "/id={app_id}/sortBy=mostRecent/page={page}/json"
)
ATOM_NS = "http://www.w3.org/2005/Atom"
ITUNES_NS = "http://itunes.apple.com/rss"


def _parse_review_date(value: str) -> date:
    if not value:
        return date.today()
    try:
        if "T" in value:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
        return datetime.strptime(value[:10], "%Y-%m-%d").date()
    except ValueError:
        return date.today()


def parse_app_store_json(payload: dict[str, Any], app_id: str) -> list[Review]:
    """Parse iTunes customer reviews JSON feed."""
    reviews: list[Review] = []
    feed = payload.get("feed") or {}
    entries = feed.get("entry") or []
    if isinstance(entries, dict):
        entries = [entries]

    for entry in entries:
        if not isinstance(entry, dict):
            continue
        # First entry is often app metadata, not a review
        if "im:rating" not in entry:
            continue
        rating_raw = entry.get("im:rating", {}).get("label", "0")
        review_id = str(entry.get("id", {}).get("label", ""))
        if not review_id:
            review_id = f"app_store_{app_id}_{entry.get('updated', {}).get('label', '')}"

        reviews.append(
            Review(
                source=ReviewSource.APP_STORE,
                review_id=review_id,
                rating=int(rating_raw),
                title=str(entry.get("title", {}).get("label", "")),
                body=str(entry.get("content", {}).get("label", "")),
                review_date=_parse_review_date(
                    str(entry.get("updated", {}).get("label", ""))
                ),
                author=str(entry.get("author", {}).get("name", {}).get("label", "")) or None,
                app_version=str(entry.get("im:version", {}).get("label", "")) or None,
            )
        )
    return reviews


def _find_child(entry: ET.Element, local_name: str) -> ET.Element | None:
    for child in entry:
        tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        if tag == local_name:
            return child
    return None


def parse_app_store_xml(xml_text: str, app_id: str) -> list[Review]:
    """Parse iTunes customer reviews Atom/XML feed (fixtures)."""
    root = ET.fromstring(xml_text)
    reviews: list[Review] = []
    for entry in root:
        tag = entry.tag.split("}")[-1] if "}" in entry.tag else entry.tag
        if tag != "entry":
            continue
        rating_el = _find_child(entry, "rating")
        if rating_el is None:
            continue
        review_id_el = _find_child(entry, "id")
        review_id = (review_id_el.text if review_id_el is not None else "") or ""
        title_el = _find_child(entry, "title")
        content_el = _find_child(entry, "content")
        updated_el = _find_child(entry, "updated")
        author_name: str | None = None
        author_el = _find_child(entry, "author")
        if author_el is not None:
            name_el = _find_child(author_el, "name")
            if name_el is not None:
                author_name = name_el.text

        reviews.append(
            Review(
                source=ReviewSource.APP_STORE,
                review_id=review_id or f"app_store_{app_id}_unknown",
                rating=int(rating_el.text or "0"),
                title=title_el.text if title_el is not None else "",
                body=content_el.text if content_el is not None else "",
                review_date=_parse_review_date(
                    updated_el.text if updated_el is not None else ""
                ),
                author=author_name,
            )
        )
    return reviews


def fetch_app_store_reviews(
    app_id: str,
    *,
    country: str = "in",
    max_pages: int = 10,
) -> list[Review]:
    """Fetch reviews from iTunes RSS (JSON). Paginates until empty or max_pages."""
    all_reviews: list[Review] = []
    seen_ids: set[str] = set()

    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        for page in range(1, max_pages + 1):
            url = ITUNES_RSS_JSON.format(country=country, page=page, app_id=app_id)
            try:
                response = client.get(url)
                response.raise_for_status()
                batch = parse_app_store_json(response.json(), app_id)
            except (httpx.HTTPError, json.JSONDecodeError) as exc:
                logger.warning("App Store page %s failed: %s", page, exc)
                break

            if not batch:
                break
            new = 0
            for r in batch:
                if r.review_id not in seen_ids:
                    seen_ids.add(r.review_id)
                    all_reviews.append(r)
                    new += 1
            if new == 0:
                break

    return all_reviews
