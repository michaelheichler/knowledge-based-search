#!/usr/bin/env python3
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server"))
import engines


GOOGLE_HTML = """
<div class="g">
  <a href="/url?q=https%3A%2F%2Fexample.com%2Fa&sa=U"><h3>Example A</h3></a>
  <div class="VwiC3b">Alpha <b>snippet</b></div>
</div>
"""

GOOGLE_JSON = """
{
  "items": [
    {
      "title": "Example JSON",
      "link": "https://example.com/json",
      "snippet": "JSON snippet"
    }
  ]
}
"""

BING_HTML = """
<li class="b_algo">
  <h2><a href="https://example.com/b">Example B</a></h2>
  <div class="b_caption"><p>Beta <strong>snippet</strong></p></div>
</li>
"""

DDG_LITE_HTML = """
<table>
  <tr><td><a href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fduckduckgo.com">DuckDuckGo</a></td></tr>
  <tr><td><a href="https://lite.duckduckgo.com/lite/">DuckDuckGo</a></td></tr>
  <tr><td><a rel="nofollow" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com%2Fd">Example D</a></td></tr>
  <tr><td class="result-snippet">Delta <b>snippet</b></td></tr>
</table>
"""

STARTPAGE_HTML = """
<style><a class="w-gl__result-title" href="https://bad.example">Bad</a></style>
<article class="w-gl__result">
  <a class="w-gl__result-title" href="/sp/result?url=https%3A%2F%2Fexample.com%2Fs">.sx{color:red}Example S</a>
  <p class="w-gl__description">Start <strong>snippet</strong></p>
</article>
"""

MOJEEK_HTML = """
<div class="result">
  <h2><a href="https://example.com/m">Example M</a></h2>
  <p class="s">Mojeek <strong>snippet</strong></p>
  <a class="ob" href="https://breadcrumb.example">breadcrumb</a>
</div>
"""

BLOCK_HTML = "<html><title>captcha</title><body>unusual traffic</body></html>"


class EngineTests(unittest.TestCase):
    def test_google_parses_fixture(self):
        original_get = engines._get
        engines._get = lambda url, timeout=engines._TIMEOUT, data=None, headers=None: GOOGLE_HTML
        try:
            hits = engines.google("example", k=5)
        finally:
            engines._get = original_get

        self.assertEqual(
            hits,
            [
                {
                    "title": "Example A",
                    "url": "https://example.com/a",
                    "snippet": "Alpha snippet",
                    "engine": "google",
                    "rank": 1,
                    "date": "",
                }
            ],
        )

    def test_google_custom_search_parses_fixture(self):
        original_get = engines._get
        engines._get = lambda url, timeout=engines._TIMEOUT, data=None, headers=None: GOOGLE_JSON
        try:
            hits = engines.google("example", k=5, config={"google_api_key": "key", "google_cx": "cx"})
        finally:
            engines._get = original_get

        self.assertEqual(hits[0]["title"], "Example JSON")
        self.assertEqual(hits[0]["url"], "https://example.com/json")
        self.assertEqual(hits[0]["snippet"], "JSON snippet")
        self.assertEqual(hits[0]["engine"], "google")

    def test_google_custom_search_falls_back_to_html(self):
        original_get = engines._get
        calls = []

        def fake_get(url, timeout=engines._TIMEOUT, data=None, headers=None):
            calls.append(url)
            if "customsearch" in url:
                raise OSError("fail")
            return GOOGLE_HTML

        engines._get = fake_get
        try:
            hits = engines.google("example", k=5, config={"google_api_key": "key", "google_cx": "cx"})
        finally:
            engines._get = original_get

        self.assertEqual(hits[0]["url"], "https://example.com/a")
        self.assertEqual(len(calls), 2)

    def test_bing_parses_fixture(self):
        original_get = engines._get
        engines._get = lambda url, timeout=engines._TIMEOUT, data=None, headers=None: BING_HTML
        try:
            hits = engines.bing("example", k=5)
        finally:
            engines._get = original_get

        self.assertEqual(hits[0]["title"], "Example B")
        self.assertEqual(hits[0]["url"], "https://example.com/b")
        self.assertEqual(hits[0]["snippet"], "Beta snippet")
        self.assertEqual(hits[0]["engine"], "bing")

    def test_duckduckgo_lite_parses_fixture(self):
        original_get = engines._get
        engines._get = lambda url, timeout=engines._TIMEOUT, data=None, headers=None: DDG_LITE_HTML
        try:
            hits = engines.duckduckgo("example", k=5)
        finally:
            engines._get = original_get

        self.assertEqual(hits[0]["title"], "Example D")
        self.assertEqual(hits[0]["url"], "https://example.com/d")
        self.assertEqual(hits[0]["snippet"], "Delta snippet")
        self.assertEqual(hits[0]["engine"], "duckduckgo")
        self.assertEqual(len(hits), 1)

    def test_startpage_parses_fixture(self):
        original_get = engines._get
        engines._get = lambda url, timeout=engines._TIMEOUT, data=None, headers=None: STARTPAGE_HTML
        try:
            hits = engines.startpage("example", k=5)
        finally:
            engines._get = original_get

        self.assertEqual(hits[0]["title"], "Example S")
        self.assertEqual(hits[0]["url"], "https://example.com/s")
        self.assertEqual(hits[0]["snippet"], "Start snippet")
        self.assertEqual(hits[0]["engine"], "startpage")
        self.assertEqual(len(hits), 1)

    def test_mojeek_parses_fixture(self):
        original_get = engines._get
        engines._get = lambda url, timeout=engines._TIMEOUT, data=None, headers=None: MOJEEK_HTML
        try:
            hits = engines.mojeek("example", k=5)
        finally:
            engines._get = original_get

        self.assertEqual(hits[0]["title"], "Example M")
        self.assertEqual(hits[0]["url"], "https://example.com/m")
        self.assertEqual(hits[0]["snippet"], "Mojeek snippet")
        self.assertEqual(hits[0]["engine"], "mojeek")

    def test_block_pages_return_empty(self):
        original_get = engines._get
        engines._get = lambda url, timeout=engines._TIMEOUT, data=None, headers=None: BLOCK_HTML
        try:
            with self.assertLogs("engines", level="WARNING") as logs:
                self.assertEqual(engines.google("example"), [])
                self.assertEqual(engines.bing("example"), [])
                self.assertEqual(engines.startpage("example"), [])
                self.assertEqual(engines.mojeek("example"), [])
        finally:
            engines._get = original_get
        self.assertEqual(
            logs.output,
            [
                "WARNING:engines:google direct scraper blocked",
                "WARNING:engines:bing direct scraper blocked",
                "WARNING:engines:startpage direct scraper blocked",
                "WARNING:engines:mojeek direct scraper blocked",
            ],
        )

    def test_search_wires_enabled_direct_engines(self):
        original_google = engines.google
        original_bing = engines.bing
        original_duckduckgo = engines.duckduckgo
        original_startpage = engines.startpage
        original_mojeek = engines.mojeek
        engines.google = lambda query, k=10, config=None: [engines.result("G", "https://g.example", "", "google", 1)]
        engines.bing = lambda query, k=10: [engines.result("B", "https://b.example", "", "bing", 1)]
        engines.duckduckgo = lambda query, k=10: []
        engines.startpage = lambda query, **options: [engines.result("S", "https://s.example", "", "startpage", 1)]
        engines.mojeek = lambda query, **options: [engines.result("M", "https://m.example", "", "mojeek", 1)]
        try:
            hits = engines.search("example", {}, k=2, cap=5)
        finally:
            engines.google = original_google
            engines.bing = original_bing
            engines.duckduckgo = original_duckduckgo
            engines.startpage = original_startpage
            engines.mojeek = original_mojeek

        self.assertEqual({hit["engine"] for hit in hits}, {"google", "bing", "startpage", "mojeek"})

    def test_parse_date_formats(self):
        self.assertEqual(engines._parse_date("16 Jun 2026"), "2026-06-16")
        self.assertEqual(engines._parse_date("7 Dec 2025"), "2025-12-07")
        self.assertEqual(engines._parse_date("May 28 2026"), "2026-05-28")
        self.assertEqual(engines._parse_date("May 28, 2026"), "2026-05-28")
        self.assertEqual(engines._parse_date("07.12.2025"), "2025-12-07")
        self.assertEqual(engines._parse_date("2026-05-28"), "2026-05-28")
        self.assertEqual(engines._parse_date("no date here"), "")

    def test_parse_date_rejects_impossible_dates(self):
        self.assertEqual(engines._parse_date("31 Feb 2026 then 7 Dec 2025"), "2025-12-07")

    def test_date_key_sorts_recent_before_old_and_undated(self):
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server"))
        import rag

        results = [
            {"date": "2025-12-07"},
            {"date": ""},
            {"date": "2026-06-16"},
        ]

        self.assertEqual([rag._date_key(result) for result in results], [-20251207, 1, -20260616])

    def test_merge_fills_empty_date_from_duplicate(self):
        primary = [engines.result("A", "https://example.com/a", "no date", "searxng", 1)]
        secondary = [engines.result("A2", "https://example.com/a/", "16 Jun 2026", "duckduckgo", 2)]

        merged = engines.merge([primary, secondary])

        self.assertEqual(merged[0]["date"], "2026-06-16")


class UrlDateTests(unittest.TestCase):
    def test_day_path(self):
        self.assertEqual(engines._parse_url_date("https://www.theverge.com/2016/3/24/1130/post"), "2016-03-24")

    def test_iso_path(self):
        self.assertEqual(engines._parse_url_date("https://glaforge.dev/posts/2026-02-10/advanced-rag"), "2026-02-10")

    def test_month_only_path(self):
        self.assertEqual(engines._parse_url_date("https://arstechnica.com/it/2016/03/rage-quit"), "2016-03-01")

    def test_rejects_impossible_date(self):
        self.assertEqual(engines._parse_url_date("https://example.com/2020/15/40/x"), "")

    def test_no_date_in_url(self):
        self.assertEqual(engines._parse_url_date("https://example.com/blog/some-post"), "")

    def test_snippet_date_preferred_over_url(self):
        hit = engines.result("t", "https://example.com/2016/03/24/x", "Published 7 Dec 2025", "searxng", 1)
        self.assertEqual(hit["date"], "2025-12-07")

    def test_url_date_fills_when_snippet_has_none(self):
        hit = engines.result("t", "https://example.com/2026/02/10/x", "no date here", "searxng", 1)
        self.assertEqual(hit["date"], "2026-02-10")


class SearchResilienceTests(unittest.TestCase):
    def test_search_survives_as_completed_timeout(self):
        from unittest import mock

        config = {"searxng_url": "x", "duckduckgo": False, "google": False, "bing": False, "startpage": False, "mojeek": False}
        real = engines.concurrent.futures.as_completed

        def flaky(futures, timeout=None):
            for future in real(futures):
                yield future
            raise engines.concurrent.futures.TimeoutError("simulated")

        with mock.patch.object(engines, "searxng", lambda *a, **k: [engines.result("A", "https://a.com", "s", "searxng", 1)]):
            with mock.patch.object(engines.concurrent.futures, "as_completed", flaky):
                hits = engines.search("q", config)

        self.assertTrue(any(hit["url"] == "https://a.com" for hit in hits))


if __name__ == "__main__":
    unittest.main()
