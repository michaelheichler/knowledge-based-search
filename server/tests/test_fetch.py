import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import fetch


class _Response:
    def __init__(self, html):
        self._html = html

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self, limit):
        return self._html.encode("utf-8")[:limit]


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

    monkeypatch.setattr(fetch.urllib.request, "urlopen", lambda request, timeout: _Response(html))

    result = fetch.fetch_clean("https://example.test/page", 1000)

    assert "Brand header should not survive" not in result
    assert "Pricing link should not survive" not in result
    assert "Footer legal text should not survive" not in result
    assert "First article paragraph with durable knowledge." in result
    assert "Second article paragraph with implementation details." in result
    assert "Important list item survives too." in result
