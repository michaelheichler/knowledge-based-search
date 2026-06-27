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
  <tr><td><a rel="nofollow" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com%2Fd">Example D</a></td></tr>
  <tr><td class="result-snippet">Delta <b>snippet</b></td></tr>
</table>
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

    def test_block_pages_return_empty(self):
        original_get = engines._get
        engines._get = lambda url, timeout=engines._TIMEOUT, data=None, headers=None: BLOCK_HTML
        try:
            with self.assertLogs("engines", level="WARNING") as logs:
                self.assertEqual(engines.google("example"), [])
                self.assertEqual(engines.bing("example"), [])
        finally:
            engines._get = original_get
        self.assertEqual(
            logs.output,
            ["WARNING:engines:google direct scraper blocked", "WARNING:engines:bing direct scraper blocked"],
        )

    def test_search_wires_enabled_direct_engines(self):
        original_google = engines.google
        original_bing = engines.bing
        original_duckduckgo = engines.duckduckgo
        engines.google = lambda query, k=10, config=None: [engines.result("G", "https://g.example", "", "google", 1)]
        engines.bing = lambda query, k=10: [engines.result("B", "https://b.example", "", "bing", 1)]
        engines.duckduckgo = lambda query, k=10: []
        try:
            hits = engines.search("example", {}, k=2, cap=5)
        finally:
            engines.google = original_google
            engines.bing = original_bing
            engines.duckduckgo = original_duckduckgo

        self.assertEqual({hit["engine"] for hit in hits}, {"google", "bing"})


if __name__ == "__main__":
    unittest.main()
