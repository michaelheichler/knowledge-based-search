import socket

import fetch
import pytest

ARTICLE_HTML = """
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


class _Response:
    def __init__(self, body, content_type="text/html", url="https://example.test/page"):
        self._body = body
        self._content_type = content_type
        self._url = url

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

    def geturl(self):
        return self._url


@pytest.fixture(autouse=True)
def public_dns(monkeypatch):
    """Resolve parser-test hosts to one public documentation address."""
    answer = (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))
    monkeypatch.setattr(fetch.socket, "getaddrinfo", lambda *args, **kwargs: [answer])


def test_fetch_clean_prefers_article_over_page_chrome(monkeypatch):
    monkeypatch.setattr(
        fetch, "_open", lambda request, timeout: _Response(ARTICLE_HTML)
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
        fetch,
        "_open",
        lambda request, timeout: _Response(
            html, content_type="text/html; charset=iso-8859-1"
        ),
    )

    result = fetch.fetch_clean("https://example.test/page", 1000)

    assert "caf\u00e9 prices" in result


def test_fetch_clean_falls_back_for_unknown_charset(monkeypatch):
    html = "<html><body><main><p>caf\u00e9 prices</p></main></body></html>"
    monkeypatch.setattr(
        fetch,
        "_open",
        lambda request, timeout: _Response(
            html, content_type="text/html; charset=not-a-real-charset"
        ),
    )

    result = fetch.fetch_clean("https://example.test/page", 1000)

    assert "caf\u00e9 prices" in result


def test_fetch_clean_returns_empty_for_pdf_magic_bytes(monkeypatch):
    monkeypatch.setattr(
        fetch,
        "_open",
        lambda request, timeout: _Response(b"%PDF-1.7\ntext"),
    )

    result = fetch.fetch_clean("https://example.test/file", 1000)

    assert result == ""


def test_fetch_clean_returns_empty_for_pdf_content_type(monkeypatch):
    monkeypatch.setattr(
        fetch,
        "_open",
        lambda request, timeout: _Response(
            "This body has readable words.", content_type="application/pdf"
        ),
    )

    result = fetch.fetch_clean("https://example.test/file", 1000)

    assert result == ""


def test_fetch_clean_skips_pdf_path_before_fetch(monkeypatch):
    def fail_urlopen(request, timeout):
        raise AssertionError("urlopen should not be called")

    monkeypatch.setattr(fetch, "_open", fail_urlopen)

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
        fetch, "_open", lambda request, timeout: _Response(html)
    )

    result = fetch.fetch_clean("https://example.test/page", 1000)

    assert result == ""


@pytest.mark.parametrize("url", ["file:///etc/passwd", "ftp://example.test/file"])
def test_fetch_clean_rejects_non_web_schemes(url):
    with pytest.raises(ValueError, match="only http and https"):
        fetch.fetch_clean(url, 1000)


@pytest.mark.parametrize(
    "address",
    ["127.0.0.1", "169.254.1.1", "10.0.0.1", "224.0.0.1", "240.0.0.1"],
)
def test_fetch_clean_rejects_special_use_addresses(monkeypatch, address):
    answer = (socket.AF_INET, socket.SOCK_STREAM, 6, "", (address, 443))
    monkeypatch.setattr(fetch.socket, "getaddrinfo", lambda *args, **kwargs: [answer])
    with pytest.raises(ValueError, match="private or special-use"):
        fetch.fetch_clean("https://blocked.test/page", 1000)


def test_redirect_handler_rejects_private_target(monkeypatch):
    answer = (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 80))
    monkeypatch.setattr(fetch.socket, "getaddrinfo", lambda *args, **kwargs: [answer])
    handler = fetch._SafeRedirectHandler()
    with pytest.raises(ValueError, match="private or special-use"):
        handler.redirect_request(None, None, 302, "Found", {}, "http://internal.test/")


def test_private_escape_hatch_allows_intranet_fetch(monkeypatch):
    monkeypatch.setenv("KBS_ALLOW_PRIVATE", "1")
    response = _Response(ARTICLE_HTML, url="http://127.0.0.1/")
    monkeypatch.setattr(fetch, "_open", lambda request, timeout: response)
    assert "Useful guide" in fetch.fetch_clean("http://127.0.0.1/", 1000)
