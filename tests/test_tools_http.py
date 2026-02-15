"""
Тесты инструмента http_request (SSRF защита).
"""

import responses

from agent.tools import http_request


def test_http_forbidden_localhost():
    """Запрет запроса к localhost."""
    out = http_request.invoke({"url": "http://127.0.0.1/", "method": "GET"})
    assert "запрещён" in out.lower() or "forbidden" in out.lower()


@responses.activate
def test_http_safe_url():
    """Разрешён публичный URL (мок)."""
    responses.add(responses.GET, "https://httpbin.org/get", json={"ok": True})
    out = http_request.invoke({"url": "https://httpbin.org/get", "method": "GET"})
    # Должен выполниться запрос (с responses)
    assert "status_code" in out or "200" in out or "ok" in out.lower()
