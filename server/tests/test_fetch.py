import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import fetch


class _Response:
    def __init__(self, body, content_type="text/html"):
        self._body = body
        self._content_type = content_type

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self, limit):
        body = self._body
        if isinstance(body, str):
            body = body.encode("utf-8")
        return body[:limit]

    def getheader(self, name, default=None):
        if name.lower() == "content-type":
            return self._content_type
        return default


def test_fetch_clean_prefers_article_over_page_chrome(monkeypatch):
    html = """
    <html>
      <body>
        <header>Brand header should not survive</header>
        <nav><a href="/pricing">Pricing link should not survive</a></nav>
        <article>
          <h1>Useful guide</h1>
          <p>First article paragraph with durable knowledge.</p>
          <p>Second article paragraph with implementation details.</p>
          <ul><li>Important list item survives too.</li></ul>
        </article>
        <footer>Footer legal text should not survive</footer>
      </body>
    </html>
    """

    monkeypatch.setattr(
        fetch.urllib.request, "urlopen", lambda request, timeout: _Response(html)
    )

    result = fetch.fetch_clean("https://example.test/page", 1000)

    assert "Brand header should not survive" not in result
    assert "Pricing link should not survive" not in result
    assert "Footer legal text should not survive" not in result
    assert "First article paragraph with durable knowledge." in result
    assert "Second article paragraph with implementation details." in result
    assert "Important list item survives too." in result


def test_fetch_clean_uses_declared_charset(monkeypatch):
    html = b"<html><body><main><p>caf\xe9 prices</p></main></body></html>"
    monkeypatch.setattr(
        fetch.urllib.request,
        "urlopen",
        lambda request, timeout: _Response(
            html, content_type="text/html; charset=iso-8859-1"
        ),
    )

    result = fetch.fetch_clean("https://example.test/page", 1000)

    assert "caf\u00e9 prices" in result


def test_fetch_clean_falls_back_for_unknown_charset(monkeypatch):
    html = "<html><body><main><p>caf\u00e9 prices</p></main></body></html>"
    monkeypatch.setattr(
        fetch.urllib.request,
        "urlopen",
        lambda request, timeout: _Response(
            html, content_type="text/html; charset=not-a-real-charset"
        ),
    )

    result = fetch.fetch_clean("https://example.test/page", 1000)

    assert "caf\u00e9 prices" in result


def test_fetch_clean_returns_empty_for_pdf_magic_bytes(monkeypatch):
    monkeypatch.setattr(
        fetch.urllib.request,
        "urlopen",
        lambda request, timeout: _Response(b"%PDF-1.7\ntext"),
    )

    result = fetch.fetch_clean("https://example.test/file", 1000)

    assert result == ""


def test_fetch_clean_returns_empty_for_pdf_content_type(monkeypatch):
    monkeypatch.setattr(
        fetch.urllib.request,
        "urlopen",
        lambda request, timeout: _Response(
            "This body has readable words.", content_type="application/pdf"
        ),
    )

    result = fetch.fetch_clean("https://example.test/file", 1000)

    assert result == ""


def test_fetch_clean_skips_pdf_path_before_fetch(monkeypatch):
    def fail_urlopen(request, timeout):
        raise AssertionError("urlopen should not be called")

    monkeypatch.setattr(fetch.urllib.request, "urlopen", fail_urlopen)

    result = fetch.fetch_clean("https://example.test/file.pdf?download=1", 1000)

    assert result == ""


def test_fetch_clean_returns_empty_for_link_heavy_nav(monkeypatch):
    html = """
    <html>
      <body>
        <nav>
          <a href="/a">Alpha menu</a>
          <a href="/b">Beta menu</a>
          <a href="/c">Gamma menu</a>
        </nav>
      </body>
    </html>
    """
    monkeypatch.setattr(
        fetch.urllib.request, "urlopen", lambda request, timeout: _Response(html)
    )

    result = fetch.fetch_clean("https://example.test/page", 1000)

    assert result == ""
