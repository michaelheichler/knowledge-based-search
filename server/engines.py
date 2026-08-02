"""Provider isolation keeps blocked and failed engines visible to callers."""

import concurrent.futures
import datetime
import html
import json
import logging
import random
import re
import threading
import time
import urllib.parse
import urllib.request

import engine_state

BROWSER_UA = (
    "Mozilla/5.0 (X11 Linux x86_64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)
_TIMEOUT = 12.0
_PROVIDER_FAILURES = (Exception,)
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


class ProviderBlocked(RuntimeError):
    """Signal that a provider returned an anti-automation page."""


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


def searxng(query, base, k=10, timeout=_TIMEOUT) -> list:
    """Query one SearXNG provider."""
    params = urllib.parse.urlencode({"q": query, "format": "json"})
    payload = json.loads(_get(f"{base.rstrip('/')}/search?{params}", timeout))
    hits = []
    for rank, row in enumerate(payload.get("results", [])[:k], 1):
        if row.get("url"):
            hits.append(
                result(
                    row.get("title", ""),
                    row["url"],
                    row.get("content", ""),
                    "searxng",
                    rank,
                )
            )
    return hits


def mwmbl(query, k=10, timeout=_TIMEOUT) -> list:
    """Query the keyless Mwmbl search API."""
    params = urllib.parse.urlencode({"s": query})
    payload = json.loads(_get(f"https://mwmbl.org/api/v1/search/?{params}", timeout))
    hits = []
    for rank, row in enumerate(payload[:k], 1):
        if not row.get("url"):
            continue
        title = "".join(segment.get("value", "") for segment in row.get("title", []))
        snippet = "".join(
            segment.get("value", "") for segment in row.get("extract", [])
        )
        hits.append(result(title, row["url"], snippet, "mwmbl", rank))
    return hits


def wikipedia(query, k=10, timeout=_TIMEOUT) -> list:
    """Query the keyless English Wikipedia search API."""
    params = urllib.parse.urlencode(
        {
            "action": "query",
            "list": "search",
            "format": "json",
            "srlimit": k,
            "srsearch": query,
        }
    )
    payload = json.loads(_get(f"https://en.wikipedia.org/w/api.php?{params}", timeout))
    rows = payload.get("query", {}).get("search", [])[:k]
    return [
        result(
            row["title"],
            "https://en.wikipedia.org/wiki/"
            + urllib.parse.quote(row["title"].replace(" ", "_"), safe=""),
            row.get("snippet", ""),
            "wikipedia",
            rank,
        )
        for rank, row in enumerate(rows, 1)
        if row.get("title")
    ]


def tavily(query, k=10, timeout=_TIMEOUT, config=None) -> list:
    """Query Tavily with the configured free API key."""
    request_body = json.dumps(
        {"api_key": config["tavily_api_key"], "query": query, "max_results": k}
    ).encode("utf-8")
    payload = json.loads(
        _get(
            "https://api.tavily.com/search",
            timeout,
            data=request_body,
            headers={"Content-Type": "application/json"},
        )
    )
    return [
        result(
            row.get("title", ""),
            row["url"],
            row.get("content", ""),
            "tavily",
            rank,
        )
        for rank, row in enumerate(payload.get("results", [])[:k], 1)
        if row.get("url")
    ]


def _ddg_target(href) -> str:
    href = html.unescape(href)
    if "uddg=" in href:
        query = urllib.parse.urlparse(href).query
        target = urllib.parse.parse_qs(query).get("uddg", [None])[0]
        if target:
            return target
    return urllib.parse.urljoin("https://duckduckgo.com", href)


def _parse_duckduckgo_html(body, k=10) -> list:
    hits = []
    for rank, match in enumerate(_DDG_RESULT.finditer(body), 1):
        if rank > k:
            break
        hits.append(
            result(
                match["title"],
                _ddg_target(match["href"]),
                match["snippet"],
                "duckduckgo",
                rank,
            )
        )
    return hits


def _parse_duckduckgo_lite(body, k=10) -> list:
    hits = []
    matches = list(_DDG_LITE_LINK.finditer(body))
    for match in matches:
        href = html.unescape(match["href"])
        title = _clean(match["title"])
        target = _ddg_target(href)
        resolved_host = urllib.parse.urlparse(target).hostname or ""
        if not title or title.lower() == "duckduckgo":
            continue
        if resolved_host.lower() in {"duckduckgo.com", "lite.duckduckgo.com"}:
            continue
        if title.lower() in {"next page", "previous page"}:
            continue
        next_start = next(
            (other.start() for other in matches if other.start() > match.start()),
            len(body),
        )
        snippet_match = _DDG_LITE_SNIPPET.search(body, match.end(), next_start)
        snippet = snippet_match["snippet"] if snippet_match else ""
        hits.append(result(title, target, snippet, "duckduckgo", len(hits) + 1))
        if len(hits) >= k:
            break
    return hits


def duckduckgo(query, k=10, timeout=_TIMEOUT) -> list:
    """Query both DuckDuckGo HTML endpoints before returning no matches."""
    params = urllib.parse.urlencode({"q": query})
    form = params.encode("utf-8")
    lite_blocked = False
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    try:
        body = _get(
            "https://lite.duckduckgo.com/lite/", timeout, data=form, headers=headers
        )
        hits = _parse_duckduckgo_lite(body, k)
        if hits:
            return hits
        _raise_if_blocked(body, "duckduckgo", hits)
    except ProviderBlocked:
        lite_blocked = True
    except OSError:
        pass
    body = _get(f"https://html.duckduckgo.com/html/?{params}", timeout)
    hits = _parse_duckduckgo_html(body, k)
    _raise_if_blocked(body, "duckduckgo", hits)
    if lite_blocked and not hits:
        raise ProviderBlocked("duckduckgo")
    return hits


def _google_target(href) -> str:
    href = html.unescape(href)
    if href.startswith("/url?"):
        target = urllib.parse.parse_qs(urllib.parse.urlparse(href).query).get(
            "q", [None]
        )[0]
        if target:
            return target
    return href


def _parse_google_html(body, k=10) -> list:
    hits = []
    matches = list(_GOOGLE_LINK.finditer(body))
    for match in matches:
        target = _google_target(match["href"])
        if not target.startswith("http"):
            continue
        next_start = next(
            (other.start() for other in matches if other.start() > match.start()),
            len(body),
        )
        snippet_match = _GOOGLE_SNIPPET.search(body, match.end(), next_start)
        snippet = snippet_match["snippet"] if snippet_match else ""
        hits.append(result(match["title"], target, snippet, "google", len(hits) + 1))
        if len(hits) >= k:
            break
    return hits


def _parse_google_json(payload, k=10) -> list:
    hits = []
    for item in payload.get("items", [])[:k]:
        if item.get("link"):
            hits.append(
                result(
                    item.get("title", ""),
                    item["link"],
                    item.get("snippet", ""),
                    "google",
                    len(hits) + 1,
                )
            )
    return hits


def _google_api(query, k, timeout, config):
    if not config or not config.get("google_api_key") or not config.get("google_cx"):
        return None
    params = urllib.parse.urlencode(
        {
            "key": config["google_api_key"],
            "cx": config["google_cx"],
            "q": query,
            "num": min(k, 10),
        }
    )
    payload = _get(
        f"https://customsearch.googleapis.com/customsearch/v1?{params}", timeout
    )
    return _parse_google_json(json.loads(payload), k)


def google(query, k=10, timeout=_TIMEOUT, config=None) -> list:
    """Query configured Google API access or the direct HTML endpoint."""
    try:
        api_hits = _google_api(query, k, timeout, config)
        if api_hits is not None:
            return api_hits
    except (OSError, ValueError, TypeError):
        pass
    params = urllib.parse.urlencode({"q": query, "num": k})
    body = _get(
        f"https://www.google.com/search?{params}",
        timeout,
        headers={"Cookie": "CONSENT=YES+"},
    )
    hits = _parse_google_html(body, k)
    _raise_if_blocked(body, "google", hits)
    return hits


def _parse_bing_html(body, k=10) -> list:
    hits = []
    for block_match in _BING_BLOCK.finditer(body):
        link_match = _BING_LINK.search(block_match["body"])
        caption_match = _BING_CAPTION.search(block_match["body"])
        snippet_match = (
            _BING_SNIPPET.search(caption_match["body"]) if caption_match else None
        )
        if link_match:
            snippet = snippet_match["snippet"] if snippet_match else ""
            hits.append(
                result(
                    link_match["title"],
                    html.unescape(link_match["href"]),
                    snippet,
                    "bing",
                    len(hits) + 1,
                )
            )
        if len(hits) >= k:
            break
    return hits or _parse_bing_legacy(body, k)


def _parse_bing_legacy(body, k):
    hits = []
    for rank, match in enumerate(_BING_LEGACY_RESULT.finditer(body), 1):
        if rank > k:
            break
        hits.append(
            result(
                match["title"],
                html.unescape(match["href"]),
                match["snippet"],
                "bing",
                rank,
            )
        )
    return hits


def bing(query, k=10, timeout=_TIMEOUT) -> list:
    """Query the Bing HTML endpoint."""
    params = urllib.parse.urlencode({"q": query})
    body = _get(f"https://www.bing.com/search?{params}", timeout)
    hits = _parse_bing_html(body, k)
    _raise_if_blocked(body, "bing", hits)
    return hits


def _clean_startpage_title(title) -> str:
    cleaned = _clean(title)
    return re.sub(r"^(?:[.#][^{]{1,80}\{[^{}]*\}\s*)+", "", cleaned).strip()


def _parse_startpage_html(body, limit=10) -> list:
    hits = []
    scrubbed_body = re.sub(
        r"<(?:style|script)\b[^>]*>.*?</(?:style|script)>",
        "",
        body,
        flags=re.DOTALL | re.IGNORECASE,
    )
    for match in _STARTPAGE_LINK.finditer(scrubbed_body):
        attrs = match["attrs"]
        class_name = _attr(attrs, "class")
        if "result" not in class_name and "w-gl__result-title" not in class_name:
            continue
        title = _clean_startpage_title(match["title"])
        href = _attr(attrs, "href")
        if not title or not href:
            continue
        snippet_match = _STARTPAGE_SNIPPET.search(match["tail"])
        snippet = snippet_match["snippet"] if snippet_match else ""
        url = _redirect_target(href, "https://www.startpage.com", ("url", "u"))
        if url.startswith("http"):
            hits.append(result(title, url, snippet, "startpage", len(hits) + 1))
        if len(hits) >= limit:
            break
    return hits


def startpage(query, timeout=_TIMEOUT, **options) -> list:
    limit = options.get("k", 10)
    params = urllib.parse.urlencode({"query": query})
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml,*/*",
        "Accept-Language": "en-US,en",
    }
    body = _get(
        f"https://www.startpage.com/sp/search?{params}", timeout, headers=headers
    )
    hits = _parse_startpage_html(body, limit)
    _raise_if_blocked(body, "startpage", hits)
    return hits


def _parse_mojeek_html(body, limit=10) -> list:
    hits = []
    for match in _MOJEEK_RESULT.finditer(body):
        href = _attr(match["attrs"], "href")
        title = _clean(match["title"])
        if not href or not title:
            continue
        snippet_match = _MOJEEK_SNIPPET.search(match["tail"])
        snippet = snippet_match["snippet"] if snippet_match else ""
        url = _absolute_url(href, "https://www.mojeek.com")
        if url.startswith("http"):
            hits.append(result(title, url, snippet, "mojeek", len(hits) + 1))
        if len(hits) >= limit:
            break
    return hits


def mojeek(query, timeout=_TIMEOUT, **options) -> list:
    limit = options.get("k", 10)
    params = urllib.parse.urlencode({"q": query})
    body = _get(f"https://www.mojeek.com/search?{params}", timeout)
    hits = _parse_mojeek_html(body, limit)
    _raise_if_blocked(body, "mojeek", hits)
    return hits


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
        "duckduckgo": lambda: duckduckgo(query, k),
        "google": lambda: google(query, k, config=config),
        "bing": lambda: bing(query, k),
        "startpage": lambda: startpage(query, k=k),
        "mojeek": lambda: mojeek(query, k=k),
        "mwmbl": lambda: mwmbl(query, k=k),
        "wikipedia": lambda: wikipedia(query, k=k),
    }
    if config.get("tavily_api_key"):
        callables["tavily"] = lambda: tavily(query, k=k, config=config)
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


_MIN_INTERVAL = 2.0
_MAX_JITTER = 2.0
_COOLDOWN_SECONDS = 1800.0
_CACHE_TTL = 600.0
_CACHE_CAP = 128
_pace_lock = threading.Lock()
_query_cache: dict = {}


def _reserve_slot(name) -> float:
    """Slots are reserved under the lock because parallel rounds would otherwise share one."""
    with _pace_lock:
        now = time.time()
        interval = _MIN_INTERVAL + random.uniform(0.0, _MAX_JITTER)
        start = engine_state.reserve_slot(name, now, interval)
        return max(0.0, start - now)


def _cached_call(name, query, k, thunk) -> list:
    """Repeat queries are served from cache because burst traffic gets providers banned."""
    key = (name, query, k)
    with _pace_lock:
        entry = _query_cache.get(key)
        if entry and time.monotonic() - entry[0] < _CACHE_TTL:
            return [dict(hit) for hit in entry[1]]
    time.sleep(_reserve_slot(name))
    hits = thunk()
    with _pace_lock:
        _query_cache[key] = (time.monotonic(), [dict(hit) for hit in hits])
        while len(_query_cache) > _CACHE_CAP:
            _query_cache.pop(next(iter(_query_cache)))
    return hits


def _build_tasks(query, config, k, outcomes=None) -> dict:
    """Cooldown outcomes stay visible because skipped providers never create futures."""
    enabled = {}
    if config.get("searxng_url"):
        enabled["searxng"] = lambda: searxng(query, config["searxng_url"], k)
    for name, thunk in _direct_callables(query, config, k).items():
        if config.get(name, _DIRECT_DEFAULTS[name]):
            enabled[name] = thunk
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


def _task_outcome(name, future) -> tuple[list, dict]:
    try:
        hits = future.result()
        return hits, {"status": "ok", "count": len(hits)}
    except ProviderBlocked as exc:
        engine_state.block_provider(name, time.time() + _COOLDOWN_SECONDS)
        return [], {"status": "error", "error": type(exc).__name__}
    except _PROVIDER_FAILURES as exc:
        return [], {"status": "error", "error": type(exc).__name__}


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


def search(query, config, k=10, cap=20) -> list:
    """Query only enabled providers and merge their results."""
    outcomes = {}
    tasks = _build_tasks(query, config, k, outcomes)
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
    assert _parse_duckduckgo_html(sample)[0]["url"] == "https://ok.com", (
        "ddg html decode failed"
    )
    lite = '<table><tr><td><a href="https://lite.duckduckgo.com/lite/">DuckDuckGo</a></td></tr><tr><td><a href="//duckduckgo.com/l/?uddg=https%3A%2F%2Flite.com">Lite</a></td></tr><tr><td class="result-snippet">lite <b>snip</b></td></tr></table>'
    lite_hits = _parse_duckduckgo_lite(lite)
    assert len(lite_hits) == 1 and lite_hits[0]["snippet"] == "lite snip", (
        "ddg lite parse failed"
    )


def _demo_parsers() -> None:
    _demo_duckduckgo_parsers()
    google_html = '<a href="/url?q=https%3A%2F%2Fg.com&sa=U"><h3>G</h3></a><div class="VwiC3b">gs</div>'
    assert _parse_google_html(google_html)[0]["url"] == "https://g.com", (
        "google html parse failed"
    )
    assert (
        _parse_google_json(
            {"items": [{"title": "GJ", "link": "https://gj.com", "snippet": "gjs"}]}
        )[0]["title"]
        == "GJ"
    ), "google json parse failed"
    bing_html = '<li class="b_algo"><h2><a href="https://b.com">B</a></h2><div class="b_caption"><p>bs</p></div></li>'
    assert _parse_bing_html(bing_html)[0]["snippet"] == "bs", "bing parse failed"
    startpage_html = '<style><a class="w-gl__result-title" href="https://bad.example">Bad</a></style><a class="w-gl__result-title" href="/sp/result?url=https%3A%2F%2Fs.com">.sx{color:red}S</a><p class="w-gl__description">ss</p>'
    startpage_hits = _parse_startpage_html(startpage_html)
    assert len(startpage_hits) == 1 and startpage_hits[0]["title"] == "S", (
        "startpage parse failed"
    )
    mojeek_html = '<h2><a href="https://m.com">M</a></h2><p class="s">ms</p><a href="https://crumb.com">crumb</a>'
    assert _parse_mojeek_html(mojeek_html)[0]["url"] == "https://m.com", (
        "mojeek parse failed"
    )


def demo() -> None:
    _demo_merge_and_dates()
    _demo_parsers()
    print("demo ok")


if __name__ == "__main__":
    demo()
