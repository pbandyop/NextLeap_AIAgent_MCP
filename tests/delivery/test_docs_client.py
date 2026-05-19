import pytest

from pulse_agent.phases.phase_04_docs_mcp.client import WorkspaceHttpClient, WorkspaceMcpError


def test_append_to_doc_success(monkeypatch):
    import httpx

    calls: list[str] = []

    class FakeClient:
        def __init__(self, *args, **kwargs):
            self.timeout = kwargs.get("timeout")

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def get(self, url):
            calls.append("get")
            request = httpx.Request("GET", url)
            return httpx.Response(200, json={"message": "ok"}, request=request)

        def post(self, url, json=None):
            calls.append("post")
            request = httpx.Request("POST", url)
            return httpx.Response(
                200,
                json={
                    "status": "success",
                    "message": "Content appended",
                    "document_id": json["doc_id"],
                },
                request=request,
            )

    import pulse_agent.phases.phase_04_docs_mcp.client as client_mod

    monkeypatch.setattr(client_mod.httpx, "Client", FakeClient)
    ws = WorkspaceHttpClient("https://example.test")
    ws.health_check()
    result = ws.append_to_doc("doc-1", "hello")
    assert result["status"] == "success"
    assert calls == ["get", "post"]


def test_append_to_doc_error_status(monkeypatch):
    import httpx

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def get(self, url):
            request = httpx.Request("GET", url)
            return httpx.Response(200, json={}, request=request)

        def post(self, url, json=None):
            request = httpx.Request("POST", url)
            return httpx.Response(
                200,
                json={"status": "error", "message": "API fail"},
                request=request,
            )

    import pulse_agent.phases.phase_04_docs_mcp.client as client_mod

    monkeypatch.setattr(client_mod.httpx, "Client", FakeClient)
    with pytest.raises(WorkspaceMcpError):
        WorkspaceHttpClient("https://example.test").append_to_doc("d", "c")
