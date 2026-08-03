import json
import os
import subprocess
import sys
import unittest
from unittest import mock

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
_PROVIDER_NAMES = (
    "searxng",
    "duckduckgo",
    "google",
    "bing",
    "startpage",
    "mojeek",
    "mwmbl",
    "wikipedia",
)


def _provider_mocks():
    providers = {}
    for name in _PROVIDER_NAMES:
        hit = engines.result(name, f"https://{name}.example", "", name, 1)
        providers[name] = mock.Mock(return_value=[hit])
    return providers


def _assert_provider_blocked(test_case, provider) -> None:
    with test_case.assertRaises(engines.ProviderBlocked):
        provider("example")


class EngineTests(unittest.TestCase):
    def test_google_parses_fixture(self) -> None:
        original_get = engines._get
        engines._get = lambda url, timeout=engines._TIMEOUT, data=None, headers=None: (
            GOOGLE_HTML
        )
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

    def test_block_marker_inside_valid_result_is_not_failure(self) -> None:
        body = GOOGLE_HTML.replace("Alpha <b>snippet</b>", "automated queries guide")
        with mock.patch.object(engines, "_get", return_value=body):
            hits = engines.google("example", k=5)

        self.assertEqual(hits[0]["snippet"], "automated queries guide")

    def test_google_custom_search_parses_fixture(self) -> None:
        original_get = engines._get
        engines._get = lambda url, timeout=engines._TIMEOUT, data=None, headers=None: (
            GOOGLE_JSON
        )
        try:
            hits = engines.google(
                "example", k=5, config={"google_api_key": "key", "google_cx": "cx"}
            )
        finally:
            engines._get = original_get

        self.assertEqual(hits[0]["title"], "Example JSON")
        self.assertEqual(hits[0]["url"], "https://example.com/json")
        self.assertEqual(hits[0]["snippet"], "JSON snippet")
        self.assertEqual(hits[0]["engine"], "google")

    def test_google_custom_search_falls_back_to_html(self) -> None:
        original_get = engines._get
        calls = []

        def fake_get(url, timeout=engines._TIMEOUT, data=None, headers=None) -> str:
            calls.append(url)
            if "customsearch" in url:
                raise OSError("fail")
            return GOOGLE_HTML

        engines._get = fake_get
        try:
            hits = engines.google(
                "example", k=5, config={"google_api_key": "key", "google_cx": "cx"}
            )
        finally:
            engines._get = original_get

        self.assertEqual(hits[0]["url"], "https://example.com/a")
        self.assertEqual(len(calls), 2)

    def test_bing_parses_fixture(self) -> None:
        original_get = engines._get
        engines._get = lambda url, timeout=engines._TIMEOUT, data=None, headers=None: (
            BING_HTML
        )
        try:
            hits = engines.bing("example", k=5)
        finally:
            engines._get = original_get

        self.assertEqual(hits[0]["title"], "Example B")
        self.assertEqual(hits[0]["url"], "https://example.com/b")
        self.assertEqual(hits[0]["snippet"], "Beta snippet")
        self.assertEqual(hits[0]["engine"], "bing")

    def test_duckduckgo_lite_parses_fixture(self) -> None:
        original_get = engines._get
        engines._get = lambda url, timeout=engines._TIMEOUT, data=None, headers=None: (
            DDG_LITE_HTML
        )
        try:
            hits = engines.duckduckgo("example", k=5)
        finally:
            engines._get = original_get

        self.assertEqual(hits[0]["title"], "Example D")
        self.assertEqual(hits[0]["url"], "https://example.com/d")
        self.assertEqual(hits[0]["snippet"], "Delta snippet")
        self.assertEqual(hits[0]["engine"], "duckduckgo")
        self.assertEqual(len(hits), 1)

    def test_duckduckgo_protocol_relative_target_gets_https_url(self) -> None:
        self.assertEqual(engines._ddg_target("//host.test/p"), "https://host.test/p")

    def test_duckduckgo_lite_protocol_relative_target_gets_https_url(self) -> None:
        body = '<table><tr><td><a href="//host.test/p">Host</a></td></tr><tr><td class="result-snippet">Snippet</td></tr></table>'

        hits = engines._parse_duckduckgo_lite(body)

        self.assertEqual(hits[0]["url"], "https://host.test/p")

    def test_startpage_parses_fixture(self) -> None:
        original_get = engines._get
        engines._get = lambda url, timeout=engines._TIMEOUT, data=None, headers=None: (
            STARTPAGE_HTML
        )
        try:
            hits = engines.startpage("example", k=5)
        finally:
            engines._get = original_get

        self.assertEqual(hits[0]["title"], "Example S")
        self.assertEqual(hits[0]["url"], "https://example.com/s")
        self.assertEqual(hits[0]["snippet"], "Start snippet")
        self.assertEqual(hits[0]["engine"], "startpage")
        self.assertEqual(len(hits), 1)

    def test_mojeek_parses_fixture(self) -> None:
        original_get = engines._get
        engines._get = lambda url, timeout=engines._TIMEOUT, data=None, headers=None: (
            MOJEEK_HTML
        )
        try:
            hits = engines.mojeek("example", k=5)
        finally:
            engines._get = original_get

        self.assertEqual(hits[0]["title"], "Example M")
        self.assertEqual(hits[0]["url"], "https://example.com/m")
        self.assertEqual(hits[0]["snippet"], "Mojeek snippet")
        self.assertEqual(hits[0]["engine"], "mojeek")

    def test_block_pages_raise_provider_failure(self) -> None:
        original_get = engines._get
        engines._get = lambda url, timeout=engines._TIMEOUT, data=None, headers=None: (
            BLOCK_HTML
        )
        providers = (
            engines.google,
            engines.bing,
            engines.startpage,
            engines.mojeek,
            engines.duckduckgo,
        )
        self.addCleanup(setattr, engines, "_get", original_get)
        with self.assertLogs("engines", level="WARNING") as logs:
            for provider in providers:
                _assert_provider_blocked(self, provider)
        self.assertTrue(all("direct scraper blocked" in item for item in logs.output))

    def test_blocked_lite_then_empty_html_is_still_failure(self) -> None:
        responses = [BLOCK_HTML, "<html></html>"]
        with (
            mock.patch.object(engines, "_get", side_effect=responses),
            self.assertRaises(engines.ProviderBlocked),
        ):
            engines.duckduckgo("example")


class SearchOutcomeTests(unittest.TestCase):
    def test_search_defaults_to_searxng_and_duckduckgo_only(self) -> None:
        providers = _provider_mocks()
        config = {"searxng_url": "https://search.test", "duckduckgo": True}
        with mock.patch.multiple(engines, **providers):
            hits = engines.search("example", config, k=2, cap=5)

        self.assertEqual(
            {hit["engine"] for hit in hits},
            {"searxng", "duckduckgo", "mwmbl", "wikipedia"},
        )
        providers["searxng"].assert_called_once()
        providers["duckduckgo"].assert_called_once()
        for name in ("google", "bing", "startpage", "mojeek"):
            providers[name].assert_not_called()

    def test_search_wires_opted_in_direct_engines(self) -> None:
        providers = _provider_mocks()
        config = {
            "duckduckgo": False,
            "google": True,
            "bing": True,
            "startpage": True,
            "mojeek": True,
        }
        with mock.patch.multiple(engines, **providers):
            hits = engines.search("example", config, k=2, cap=10)

        expected = {"google", "bing", "startpage", "mojeek", "mwmbl", "wikipedia"}
        self.assertEqual({hit["engine"] for hit in hits}, expected)
        providers["duckduckgo"].assert_not_called()

    def test_disabled_engines_are_never_fallback_targets(self) -> None:
        providers = _provider_mocks()
        providers["searxng"].return_value = []
        providers["duckduckgo"].return_value = []
        config = {
            "searxng_url": "https://search.test",
            "duckduckgo": True,
            "mwmbl": False,
            "wikipedia": False,
        }
        with mock.patch.multiple(engines, **providers):
            hits = engines.search("example", config, k=2, cap=5)

        self.assertEqual(hits, [])
        for name in ("google", "bing", "startpage", "mojeek", "mwmbl", "wikipedia"):
            providers[name].assert_not_called()
        self.assertEqual(hits.outcomes["searxng"]["status"], "ok")
        self.assertEqual(hits.outcomes["duckduckgo"]["status"], "ok")

    def test_merged_json_keeps_provider_provenance(self) -> None:
        providers = _provider_mocks()
        shared = "https://shared.example/Case?Q=Value"
        providers["searxng"].return_value = [
            engines.result("S", shared, "", "searxng", 1)
        ]
        providers["duckduckgo"].return_value = [
            engines.result("D", shared, "", "duckduckgo", 2)
        ]
        config = {
            "searxng_url": "https://search.test",
            "duckduckgo": True,
            "mwmbl": False,
            "wikipedia": False,
        }
        with mock.patch.multiple(engines, **providers):
            hits = engines.search("example", config)

        payload = json.loads(json.dumps(hits))
        self.assertEqual(payload[0]["engines"], ["searxng", "duckduckgo"])
        self.assertEqual(set(hits.outcomes), {"searxng", "duckduckgo"})

    def test_partial_provider_failure_is_structured(self) -> None:
        providers = _provider_mocks()
        providers["searxng"].side_effect = OSError("https://secret.test failed")
        config = {
            "searxng_url": "https://search.test",
            "duckduckgo": True,
            "mwmbl": False,
            "wikipedia": False,
        }
        with mock.patch.multiple(engines, **providers):
            hits = engines.search("example", config)

        self.assertEqual(hits.outcomes["searxng"]["status"], "error")
        self.assertEqual(hits.outcomes["searxng"]["error"], "OSError")
        self.assertNotIn("secret.test", json.dumps(hits.outcomes))
        self.assertEqual(hits.outcomes["duckduckgo"]["status"], "ok")
        self.assertTrue(hits)

    def test_all_provider_failures_raise_network_error(self) -> None:
        providers = _provider_mocks()
        providers["duckduckgo"].side_effect = OSError("offline")
        with (
            mock.patch.multiple(engines, **providers),
            self.assertRaises(engines.AllProvidersFailed),
        ):
            engines.search(
                "example",
                {"duckduckgo": True, "mwmbl": False, "wikipedia": False},
            )

    def test_malformed_provider_shape_completes_future_with_error(self) -> None:
        config = {
            "searxng_url": "https://search.test",
            "duckduckgo": False,
            "mwmbl": False,
            "wikipedia": False,
        }
        with (
            mock.patch.object(engines, "_get", return_value="[]"),
            self.assertRaises(engines.AllProvidersFailed) as caught,
        ):
            engines.search("example", config)

        outcome = caught.exception.outcomes["searxng"]
        self.assertEqual(outcome["error"], "AttributeError")

    def test_blocked_duckduckgo_is_a_network_failure(self) -> None:
        with (
            mock.patch.object(engines, "_get", return_value=BLOCK_HTML),
            self.assertRaises(engines.AllProvidersFailed) as caught,
        ):
            engines.search(
                "example",
                {"duckduckgo": True, "mwmbl": False, "wikipedia": False},
            )

        outcome = caught.exception.outcomes["duckduckgo"]
        self.assertEqual(outcome["status"], "error")
        self.assertEqual(outcome["error"], "ProviderBlocked")

    def test_parse_date_formats(self) -> None:
        self.assertEqual(engines._parse_date("16 Jun 2026"), "2026-06-16")
        self.assertEqual(engines._parse_date("7 Dec 2025"), "2025-12-07")
        self.assertEqual(engines._parse_date("May 28 2026"), "2026-05-28")
        self.assertEqual(engines._parse_date("May 28, 2026"), "2026-05-28")
        self.assertEqual(engines._parse_date("07.12.2025"), "2025-12-07")
        self.assertEqual(engines._parse_date("2026-05-28"), "2026-05-28")
        self.assertEqual(engines._parse_date("no date here"), "")

    def test_parse_date_rejects_impossible_dates(self) -> None:
        self.assertEqual(
            engines._parse_date("31 Feb 2026 then 7 Dec 2025"), "2025-12-07"
        )

    def test_merge_fills_empty_date_from_duplicate(self) -> None:
        primary = [
            engines.result("A", "https://example.com/a", "no date", "searxng", 1)
        ]
        secondary = [
            engines.result(
                "A2", "https://example.com/a/", "16 Jun 2026", "duckduckgo", 2
            )
        ]

        merged = engines.merge([primary, secondary])

        self.assertEqual(merged[0]["date"], "2026-06-16")


class NormUrlTests(unittest.TestCase):
    def test_norm_url_sorts_query_params(self) -> None:
        self.assertEqual(
            engines.norm_url("https://example.com/path?b=2&a=1"),
            engines.norm_url("https://example.com/path?a=1&b=2"),
        )

    def test_norm_url_preserves_path_and_query_case(self) -> None:
        normalized = engines.norm_url("HTTPS://Example.COM/CasePath?Key=Value")
        self.assertEqual(normalized, "example.com/CasePath?Key=Value")

    def test_norm_url_dedupes_http_and_https(self) -> None:
        http = engines.norm_url("http://example.com/CasePath?Key=Value")
        https = engines.norm_url("https://example.com/CasePath?Key=Value")
        self.assertEqual(http, https)

    def test_norm_url_tolerates_invalid_port_text(self) -> None:
        self.assertEqual(
            engines.norm_url("http://x.com:bad/p"),
            "x.com:bad/p",
        )


class UrlDateTests(unittest.TestCase):
    def test_day_path(self) -> None:
        self.assertEqual(
            engines._parse_url_date("https://www.theverge.com/2016/3/24/1130/post"),
            "2016-03-24",
        )

    def test_iso_path(self) -> None:
        self.assertEqual(
            engines._parse_url_date(
                "https://glaforge.dev/posts/2026-02-10/advanced-rag"
            ),
            "2026-02-10",
        )

    def test_month_only_path(self) -> None:
        self.assertEqual(
            engines._parse_url_date("https://arstechnica.com/it/2016/03/rage-quit"),
            "2016-03-01",
        )

    def test_rejects_impossible_date(self) -> None:
        self.assertEqual(
            engines._parse_url_date("https://example.com/2020/15/40/x"), ""
        )

    def test_no_date_in_url(self) -> None:
        self.assertEqual(
            engines._parse_url_date("https://example.com/blog/some-post"), ""
        )

    def test_snippet_date_preferred_over_url(self) -> None:
        hit = engines.result(
            "t",
            "https://example.com/2016/03/24/x",
            "Published 7 Dec 2025",
            "searxng",
            1,
        )
        self.assertEqual(hit["date"], "2025-12-07")

    def test_url_date_fills_when_snippet_has_none(self) -> None:
        hit = engines.result(
            "t", "https://example.com/2026/02/10/x", "no date here", "searxng", 1
        )
        self.assertEqual(hit["date"], "2026-02-10")


class SearchResilienceTests(unittest.TestCase):
    def test_task_deadline_allows_process_exit_with_hung_provider(self) -> None:
        server_dir = os.path.join(os.path.dirname(__file__), "..", "server")
        script = (
            f"import sys,time; sys.path.insert(0, {server_dir!r}); import engines; "
            "engines._TIMEOUT = -1.9; "
            "engines._run_tasks({'hung': lambda: time.sleep(5)})"
        )

        completed = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            timeout=1,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)


if __name__ == "__main__":
    unittest.main()
