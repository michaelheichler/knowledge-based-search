"""Provider isolation keeps blocked and failed engines visible to callers."""

import concurrent.futures
import datetime
import html
import logging
import random
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

import engine_pacing as _pacing
import engine_state
from library_engine import _mcp_json, _mcp_post
from library_engine import library as _library

BROWSER_UA = (
    "Mozilla/5.0 (X11 Linux x86_64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)
_TIMEOUT = 12.0
_PROVIDER_FAILURES = _pacing._PROVIDER_FAILURES
ProviderBlocked = _pacing.ProviderBlocked
_MIN_INTERVAL = _pacing._MIN_INTERVAL
_MAX_JITTER = _pacing._MAX_JITTER
_COOLDOWN_SECONDS = _pacing._COOLDOWN_SECONDS
_CACHE_TTL = _pacing._CACHE_TTL
_CACHE_CAP = _pacing._CACHE_CAP
_pace_lock = _pacing._pace_lock
_query_cache = _pacing._query_cache
_pacing.random = random
_DDG_RESULT = re.compile(
    r'result__a"[^>]*href="(?P<href>[^"]+)"[^>]*>(?P<title>.*?)</a>.*?'
    r'result__snippet"[^>]*>(?P<snippet>.*?)</a>',
    re.DOTALL,
)
_DDG_LITE_LINK = re.compile(
    r'<a[^>]+href="(?P<href>[^"]+)"[^>]*>(?P<title>.*?)</a>', re.DOTALL
)
_DDG_LITE_SNIPPET = re.compile(
    r'<td[^>]+class="[^"]*result-snippet[^"]*"[^>]*>(?P<snippet>.*?)</td>', re.DOTALL
)
_GOOGLE_LINK = re.compile(
    r'<a[^>]+href="(?P<href>[^"]+)"[^>]*>\s*<h3[^>]*>(?P<title>.*?)</h3>', re.DOTALL
)
_GOOGLE_SNIPPET = re.compile(
    r'<div[^>]+class="[^"]*\bVwiC3b\b[^"]*"[^>]*>(?P<snippet>.*?)</div>', re.DOTALL
)
_BING_BLOCK = re.compile(
    r'<li[^>]+class="[^"]*\bb_algo\b[^"]*"[^>]*>(?P<body>.*?)</li>', re.DOTALL
)
_BING_LINK = re.compile(
    r'<h2[^>]*>\s*<a[^>]+href="(?P<href>[^"]+)"[^>]*>(?P<title>.*?)</a>', re.DOTALL
)
_BING_CAPTION = re.compile(
    r'<div[^>]+class="[^"]*\bb_caption\b[^"]*"[^>]*>(?P<body>.*?)</div>', re.DOTALL
)
_BING_SNIPPET = re.compile(r"<p[^>]*>(?P<snippet>.*?)</p>", re.DOTALL)
_BING_LEGACY_RESULT = re.compile(
    r'<li[^>]+class="[^"]*\bb_algo\b[^"]*"[^>]*>.*?'
    r'<h2[^>]*>\s*<a[^>]+href="(?P<href>[^"]+)"[^>]*>(?P<title>.*?)</a>.*?</h2>.*?'
    r"<p[^>]*>(?P<snippet>.*?)</p>",
    re.DOTALL,
)
_STARTPAGE_LINK = re.compile(
    r"<a\b(?P<attrs>[^>]*)>(?P<title>.*?)</a>(?P<tail>.*?)(?=<a\b|\Z)", re.DOTALL
)
_STARTPAGE_SNIPPET = re.compile(
    r'<(?:p|div)[^>]+class="[^"]*(?:w-gl__description|description|result-desc)[^"]*"[^>]*>(?P<snippet>.*?)</(?:p|div)>',
    re.DOTALL,
)
_MOJEEK_RESULT = re.compile(
    r"<h2[^>]*>\s*<a(?P<attrs>[^>]*)>(?P<title>.*?)</a>\s*</h2>(?P<tail>.*?)(?=<h2|\Z)",
    re.DOTALL,
)
_MOJEEK_SNIPPET = re.compile(
    r'<p[^>]+class="[^"]*(?:s|snippet|result-summary)[^"]*"[^>]*>(?P<snippet>.*?)</p>',
    re.DOTALL,
)
_BLOCKED = re.compile(
    r"captcha|unusual traffic|verify you are human|automated queries|our systems have detected",
    re.IGNORECASE,
)
_LOG = logging.getLogger(__name__)


def _raise_if_blocked(body, provider, hits) -> None:
    if not hits and _BLOCKED.search(body):
        _LOG.warning("%s direct scraper blocked", provider)
        raise ProviderBlocked(provider)


_MONTHS = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}
_DATE_PATTERNS = (
    re.compile(r"\b(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})\b"),
    re.compile(
        r"\b(?P<day>\d{1,2})\s+(?P<month_name>[A-Za-z]{3,9})\s+(?P<year>\d{4})\b"
    ),
    re.compile(
        r"\b(?P<month_name>[A-Za-z]{3,9})\s+(?P<day>\d{1,2}),?\s+(?P<year>\d{4})\b"
    ),
    re.compile(r"\b(?P<day>\d{2})\.(?P<month>\d{2})\.(?P<year>\d{4})\b"),
)
_URL_DATE_PATTERNS = (
    re.compile(r"/(20\d{2})/(\d{1,2})/(\d{1,2})(?:/|\b)"),
    re.compile(r"/(20\d{2})-(\d{2})-(\d{2})(?:/|\b)"),
    re.compile(r"/(20\d{2})/(\d{1,2})(?:/|\b)"),
)


def result(title, url, snippet, engine, rank) -> dict:
    cleaned_snippet = _clean(snippet)
    return {
        "title": _clean(title),
        "url": url,
        "snippet": cleaned_snippet,
        "engine": engine,
        "rank": rank,
        "date": _parse_date(cleaned_snippet) or _parse_url_date(url),
    }


def _safe_iso_date(year, month, day="1") -> str:
    try:
        return datetime.date(int(year), int(month), int(day)).isoformat()
    except (ValueError, TypeError):
        return ""


def _parse_url_date(url) -> str:
    for pattern in _URL_DATE_PATTERNS:
        match = pattern.search(url or "")
        if not match:
            continue
        day = match.group(3) if pattern.groups > 2 else "1"
        iso = _safe_iso_date(match.group(1), match.group(2), day)
        if iso:
            return iso
    return ""


def _parse_date(text) -> str:
    matches = []
    for pattern in _DATE_PATTERNS:
        matches.extend((match.start(), match) for match in pattern.finditer(text or ""))
    for position, match in sorted(matches, key=lambda item: item[0]):
        groups = match.groupdict()
        month = groups.get("month")
        if groups.get("month_name"):
            month = _MONTHS.get(groups["month_name"].lower())
        if not month:
            continue
        iso = _safe_iso_date(groups["year"], month, groups["day"])
        if iso:
            return iso
    return ""


def _clean(text) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", text or "")).strip()


def _attr(attrs, name) -> str:
    match = re.search(rf'\b{name}="(?P<value>[^"]*)"', attrs)
    return html.unescape(match["value"]) if match else ""


def _absolute_url(href, base) -> str:
    return urllib.parse.urljoin(base, html.unescape(href))


def _redirect_target(href, base, parameter_names) -> str:
    url = _absolute_url(href, base)
    query = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    for parameter_name in parameter_names:
        target = query.get(parameter_name, [None])[0]
        if target and target.startswith("http"):
            return target
    return url


def _get(url, timeout=_TIMEOUT, data=None, headers=None) -> str:
    request_headers = {"User-Agent": BROWSER_UA}
    if headers:
        request_headers.update(headers)
    request = urllib.request.Request(url, data=data, headers=request_headers)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", "replace")


_DIRECT_NAMES = frozenset(
    {
        "searxng",
        "mwmbl",
        "wikipedia",
        "tavily",
        "duckduckgo",
        "google",
        "bing",
        "startpage",
        "mojeek",
        "_ddg_target",
        "_parse_duckduckgo_html",
        "_parse_duckduckgo_lite",
        "_google_target",
        "_parse_google_html",
        "_parse_google_json",
        "_google_api",
        "_parse_bing_html",
        "_parse_bing_legacy",
        "_clean_startpage_title",
        "_parse_startpage_html",
        "_parse_mojeek_html",
    }
)


def _direct(name: str) -> Any:
    """Load direct adapters only when a caller selects one."""
    import direct_engines

    return getattr(direct_engines, name)


def _provider(name: str) -> Any:
    """Prefer patched compatibility attributes before loading direct adapters."""
    return globals().get(name) or _direct(name)


def __getattr__(name: str) -> Any:
    if name in _DIRECT_NAMES:
        return _direct(name)
    raise AttributeError(name)


def _reserve_slot(name) -> float:
    """Keep pacing constants patchable through the legacy engines module."""
    _pacing._MIN_INTERVAL = _MIN_INTERVAL
    _pacing._MAX_JITTER = _MAX_JITTER
    return _pacing._reserve_slot(name)


def _cached_call(name, query, k, thunk) -> list:
    """Keep cache limits patchable through the legacy engines module."""
    _pacing._CACHE_TTL = _CACHE_TTL
    _pacing._CACHE_CAP = _CACHE_CAP
    return _pacing._cached_call(name, query, k, thunk)


def _task_outcome(name, future) -> tuple[list, dict]:
    """Keep cooldown limits patchable through the legacy engines module."""
    _pacing._COOLDOWN_SECONDS = _COOLDOWN_SECONDS
    return _pacing._task_outcome(name, future)


def library(query, k=10, timeout=_TIMEOUT, config=None) -> list:
    """Keep trusted library passages outside the paced network fan-out."""
    return _library(
        query,
        k=k,
        timeout=timeout,
        config=config,
        post=_mcp_post,
        parser=_mcp_json,
        result_fn=result,
    )


_SCIENCE_UA = "kbs/0.2 (keyless research CLI)"
_RATE_LIMIT_COOLDOWN = 120.0


def _api_get(url, provider, timeout=_TIMEOUT, headers=None) -> str:
    """429 maps to a short cooldown because API throttles clear in minutes, not the scraper-block half hour."""
    try:
        return _get(url, timeout, headers=headers)
    except urllib.error.HTTPError as exc:
        if exc.code == 429:
            raise ProviderBlocked(provider, cooldown=_RATE_LIMIT_COOLDOWN) from exc
        raise


def arxiv(query, k=10, timeout=_TIMEOUT) -> list:
    """Load the split adapter lazily so engines.py remains directly executable."""
    import science_engines

    return science_engines.arxiv(query, k, timeout)


def pubmed(query, k=10, timeout=_TIMEOUT) -> list:
    """Load the split adapter lazily so engines.py remains directly executable."""
    import science_engines

    return science_engines.pubmed(query, k, timeout)


def semanticscholar(query, k=10, timeout=_TIMEOUT) -> list:
    """Load the split adapter lazily so engines.py remains directly executable."""
    import science_engines

    return science_engines.semanticscholar(query, k, timeout)


def crossref(query, k=10, timeout=_TIMEOUT, config=None) -> list:
    """Load the split adapter lazily so engines.py remains directly executable."""
    import science_engines

    return science_engines.crossref(query, k, timeout, config)


SCIENTIFIC_PLATFORMS = frozenset({"arxiv", "pubmed", "semanticscholar", "crossref"})


def _scientific_callables(query, config, k) -> dict:
    """Build scientific tasks only for an explicitly filtered search."""
    return {
        "arxiv": lambda: arxiv(query, k),
        "pubmed": lambda: pubmed(query, k),
        "semanticscholar": lambda: semanticscholar(query, k),
        "crossref": lambda: crossref(query, k, config=config),
    }



def _normalized_netloc(parts) -> str:
    user_info = parts.netloc.rsplit("@", 1)[0] + "@" if "@" in parts.netloc else ""
    hostname = (parts.hostname or "").lower()
    host = f"[{hostname}]" if ":" in hostname else hostname
    try:
        port_number = parts.port
    except ValueError:
        return parts.netloc
    port = f":{port_number}" if port_number is not None else ""
    return f"{user_info}{host}{port}"


def norm_url(url) -> str:
    """Normalize URL identity without changing path or query case."""
    parts = urllib.parse.urlsplit(url)
    path = parts.path.rstrip("/")
    query = urllib.parse.urlencode(
        sorted(urllib.parse.parse_qsl(parts.query, keep_blank_values=True))
    )
    identity = f"{_normalized_netloc(parts)}{path}"
    return f"{identity}?{query}" if query else identity


def _merge_hit(by_url, hit) -> None:
    key = norm_url(hit["url"])
    existing = by_url.get(key)
    if existing is None:
        by_url[key] = {**hit, "engines": [hit["engine"]]}
        return
    existing["rank"] = min(existing["rank"], hit["rank"])
    if not existing.get("date") and hit.get("date"):
        existing["date"] = hit["date"]
    if hit["engine"] not in existing["engines"]:
        existing["engines"].append(hit["engine"])


def merge(result_lists, cap=20) -> list:
    by_url = {}
    for hits in result_lists:
        for hit in hits:
            _merge_hit(by_url, hit)
    ordered = sorted(
        by_url.values(), key=lambda hit: (hit["rank"], -len(hit["engines"]))
    )
    return ordered[:cap]


def _direct_callables(query, config, k) -> dict:
    callables = {
        "duckduckgo": lambda: _provider("duckduckgo")(query, k),
        "google": lambda: _provider("google")(query, k, config=config),
        "bing": lambda: _provider("bing")(query, k),
        "startpage": lambda: _provider("startpage")(query, k=k),
        "mojeek": lambda: _provider("mojeek")(query, k=k),
        "mwmbl": lambda: _provider("mwmbl")(query, k=k),
        "wikipedia": lambda: _provider("wikipedia")(query, k=k),
    }
    if config.get("tavily_api_key"):
        callables["tavily"] = lambda: _provider("tavily")(query, k=k, config=config)
    return callables


_DIRECT_DEFAULTS = {
    "duckduckgo": True,
    "google": False,
    "bing": False,
    "startpage": False,
    "mojeek": False,
    "mwmbl": True,
    "wikipedia": True,
    "tavily": True,
}


def _build_tasks(query, config, k, outcomes=None, providers=None) -> dict:
    """Cooldown outcomes stay visible because skipped providers never create futures."""
    enabled = {}
    if config.get("searxng_url"):
        enabled["searxng"] = lambda: _provider("searxng")(query, config["searxng_url"], k)
    for name, thunk in _direct_callables(query, config, k).items():
        if config.get(name, _DIRECT_DEFAULTS[name]):
            enabled[name] = thunk
    if providers is not None:
        enabled.update(_scientific_callables(query, config, k))
        enabled = {name: thunk for name, thunk in enabled.items() if name in providers}
    cooling = engine_state.cooling_down(enabled, time.time())
    if outcomes is not None:
        outcomes.update({name: {"status": "cooldown"} for name in cooling})
    return {
        name: lambda name=name, thunk=thunk: _cached_call(name, query, k, thunk)
        for name, thunk in enabled.items()
        if name not in cooling
    }


class SearchResults(list):
    """Merged hits with structured outcomes for every attempted provider."""

    def __init__(self, hits, outcomes):
        super().__init__(hits)
        self.outcomes = outcomes


class AllProvidersFailed(OSError):
    """Signal that every configured provider ended in an error."""

    def __init__(self, outcomes):
        super().__init__("all configured search providers failed")
        self.outcomes = outcomes


def _daemon_future(fn):
    future = concurrent.futures.Future()

    def run() -> None:
        if not future.set_running_or_notify_cancel():
            return
        try:
            future.set_result(fn())
        except _PROVIDER_FAILURES as exc:
            future.set_exception(exc)

    threading.Thread(target=run, daemon=True).start()
    return future


def _run_tasks(tasks) -> tuple[list, dict]:
    futures = {_daemon_future(fn): name for name, fn in tasks.items()}
    done, pending = concurrent.futures.wait(futures, timeout=_TIMEOUT + 2)
    results = {}
    outcomes = {}
    for future in done:
        name = futures[future]
        results[name], outcomes[name] = _task_outcome(name, future)
    for future in pending:
        name = futures[future]
        future.cancel()
        outcomes[name] = {"status": "error", "error": "aggregate timeout"}
    lists = [results.get(name, []) for name in tasks]
    return lists, outcomes


def search(query, config, k=10, cap=20, providers=None) -> list:
    """Query only enabled providers and merge their results."""
    outcomes = {}
    tasks = _build_tasks(query, config, k, outcomes, providers=providers)
    if not tasks:
        if outcomes:
            raise AllProvidersFailed(outcomes)
        return SearchResults([], outcomes)
    lists, task_outcomes = _run_tasks(tasks)
    outcomes.update(task_outcomes)
    if not any(item["status"] == "ok" for item in outcomes.values()):
        raise AllProvidersFailed(outcomes)
    return SearchResults(merge(lists, cap), outcomes)


def _demo_merge_and_dates() -> None:
    primary = [
        result("A", "https://x.com/p", "sa", "searxng", 1),
        result("B", "https://y.com", "sb", "searxng", 2),
    ]
    secondary = [result("A2", "https://X.com/p/", "sb2", "duckduckgo", 3)]
    merged = merge([primary, secondary])
    assert len(merged) == 2, merged
    assert merged[0]["rank"] == 1 and set(merged[0]["engines"]) == {
        "searxng",
        "duckduckgo",
    }, merged[0]
    assert _parse_date("16 Jun 2026") == "2026-06-16"
    assert _parse_date("May 28, 2026") == "2026-05-28"
    assert _parse_date("07.12.2025") == "2025-12-07"
    assert _parse_date("no date here") == ""


def _demo_duckduckgo_parsers() -> None:
    sample = '<a class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fok.com">Hit</a><a class="result__snippet" href="#">snip</a>'
    assert _provider("_parse_duckduckgo_html")(sample)[0]["url"] == "https://ok.com", (
        "ddg html decode failed"
    )
    lite = '<table><tr><td><a href="https://lite.duckduckgo.com/lite/">DuckDuckGo</a></td></tr><tr><td><a href="//duckduckgo.com/l/?uddg=https%3A%2F%2Flite.com">Lite</a></td></tr><tr><td class="result-snippet">lite <b>snip</b></td></tr></table>'
    lite_hits = _provider("_parse_duckduckgo_lite")(lite)
    assert len(lite_hits) == 1 and lite_hits[0]["snippet"] == "lite snip", (
        "ddg lite parse failed"
    )


def _demo_parsers() -> None:
    _demo_duckduckgo_parsers()
    google_html = '<a href="/url?q=https%3A%2F%2Fg.com&sa=U"><h3>G</h3></a><div class="VwiC3b">gs</div>'
    assert _provider("_parse_google_html")(google_html)[0]["url"] == "https://g.com", (
        "google html parse failed"
    )
    assert (
        _provider("_parse_google_json")(
            {"items": [{"title": "GJ", "link": "https://gj.com", "snippet": "gjs"}]}
        )[0]["title"]
        == "GJ"
    ), "google json parse failed"
    bing_html = '<li class="b_algo"><h2><a href="https://b.com">B</a></h2><div class="b_caption"><p>bs</p></div></li>'
    assert _provider("_parse_bing_html")(bing_html)[0]["snippet"] == "bs", "bing parse failed"
    startpage_html = '<style><a class="w-gl__result-title" href="https://bad.example">Bad</a></style><a class="w-gl__result-title" href="/sp/result?url=https%3A%2F%2Fs.com">.sx{color:red}S</a><p class="w-gl__description">ss</p>'
    startpage_hits = _provider("_parse_startpage_html")(startpage_html)
    assert len(startpage_hits) == 1 and startpage_hits[0]["title"] == "S", (
        "startpage parse failed"
    )
    mojeek_html = '<h2><a href="https://m.com">M</a></h2><p class="s">ms</p><a href="https://crumb.com">crumb</a>'
    assert _provider("_parse_mojeek_html")(mojeek_html)[0]["url"] == "https://m.com", (
        "mojeek parse failed"
    )


def demo() -> None:
    _demo_merge_and_dates()
    _demo_parsers()
    print("demo ok")


if __name__ == "__main__":
    demo()
