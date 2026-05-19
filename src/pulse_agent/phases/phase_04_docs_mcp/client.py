from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class WorkspaceMcpError(RuntimeError):
    pass


class WorkspaceHttpClient:
    """HTTP client for NextLeap Google workspace MCP server (Docs + Gmail REST)."""

    def __init__(self, base_url: str, *, timeout_seconds: float = 120.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout_seconds

    def health_check(self) -> dict[str, Any]:
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(f"{self.base_url}/")
            response.raise_for_status()
            return response.json()

    def append_to_doc(self, doc_id: str, content: str) -> dict[str, Any]:
        payload = {"doc_id": doc_id, "content": content}
        logger.info("POST %s/append_to_doc doc_id=%s bytes=%s", self.base_url, doc_id, len(content))
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(f"{self.base_url}/append_to_doc", json=payload)
        if response.status_code >= 500:
            raise WorkspaceMcpError(
                f"append_to_doc HTTP {response.status_code}: {response.text[:500]}"
            )
        data = response.json()
        status = str(data.get("status", "")).lower()
        if status == "rejected":
            raise WorkspaceMcpError(data.get("message", "append_to_doc rejected by server"))
        if status == "error":
            detail = data.get("details") or data.get("message", "unknown error")
            raise WorkspaceMcpError(f"append_to_doc failed: {detail}")
        if response.status_code >= 400:
            raise WorkspaceMcpError(f"append_to_doc HTTP {response.status_code}: {data}")
        return data

    def create_email_draft(self, to: str, subject: str, body: str) -> dict[str, Any]:
        payload = {"to": to, "subject": subject, "body": body}
        logger.info(
            "POST %s/create_email_draft to=%s subject=%r bytes=%s",
            self.base_url,
            to,
            subject,
            len(body),
        )
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(f"{self.base_url}/create_email_draft", json=payload)
        if response.status_code >= 500:
            raise WorkspaceMcpError(
                f"create_email_draft HTTP {response.status_code}: {response.text[:500]}"
            )
        data = response.json()
        status = str(data.get("status", "")).lower()
        if status == "rejected":
            raise WorkspaceMcpError(
                data.get("message", "create_email_draft rejected by server")
            )
        if status == "error":
            detail = data.get("details") or data.get("message", "unknown error")
            raise WorkspaceMcpError(f"create_email_draft failed: {detail}")
        if response.status_code >= 400:
            raise WorkspaceMcpError(f"create_email_draft HTTP {response.status_code}: {data}")
        return data
