#!/usr/bin/env python3
import concurrent.futures
import contextlib
import datetime
import html
import json
import logging
import re
import urllib.parse
import urllib.request

BROWSER_UA = (
    "Mozilla/5.0 (X11 Linux x86_64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)
_TIMEOUT = 12.0
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
    re.I,
)
_LOG = logging.getLogger(__name__)
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


# craftsman-ignore: PY001 a search hit carries all five fields
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


def _parse_url_date(url) -> str:
    for pattern in _URL_DATE_PATTERNS:
        match = pattern.search(url or "")
        if not match:
            continue
        groups = match.groups()
        day = int(groups[2]) if len(groups) > 2 else 1
        with contextlib.suppress(ValueError):
            return datetime.date(int(groups[0]), int(groups[1]), day).isoformat()
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
        with contextlib.suppress(ValueError):
            return datetime.date(
                int(groups["year"]), int(month), int(groups["day"])
            ).isoformat()
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
    params = urllib.parse.urlencode({"q": query, "format": "json"})
    try:
        payload = json.loads(_get(f"{base.rstrip('/')}/search?{params}", timeout))
    except (OSError, ValueError):
        return []
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
    params = urllib.parse.urlencode({"q": query})
    form = params.encode("utf-8")
    try:
        body = _get(
            "https://lite.duckduckgo.com/lite/",
            timeout,
            data=form,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    except OSError:
        body = ""
    hits = _parse_duckduckgo_lite(body, k)
    if hits:
        return hits
    try:
        body = _get(f"https://html.duckduckgo.com/html/?{params}", timeout)
    except OSError:
        return []
    return _parse_duckduckgo_html(body, k)


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


def _parse_google_json(body, k=10) -> list:
    payload = json.loads(body)
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


def google(query, k=10, timeout=_TIMEOUT, config=None) -> list:
    if config and config.get("google_api_key") and config.get("google_cx"):
        params = urllib.parse.urlencode(
            {
                "key": config["google_api_key"],
                "cx": config["google_cx"],
                "q": query,
                "num": min(k, 10),
            }
        )
        try:
            return _parse_google_json(
                _get(
                    f"https://customsearch.googleapis.com/customsearch/v1?{params}",
                    timeout,
                ),
                k,
            )
        except (OSError, ValueError, TypeError):
            pass
    params = urllib.parse.urlencode({"q": query, "num": k})
    try:
        body = _get(
            f"https://www.google.com/search?{params}",
            timeout,
            headers={"Cookie": "CONSENT=YES+"},
        )
    except OSError:
        return []
    if _BLOCKED.search(body):
        _LOG.warning("google direct scraper blocked")
        return []
    return _parse_google_html(body, k)


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
    if hits:
        return hits
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
    params = urllib.parse.urlencode({"q": query})
    try:
        body = _get(f"https://www.bing.com/search?{params}", timeout)
    except OSError:
        return []
    if _BLOCKED.search(body):
        _LOG.warning("bing direct scraper blocked")
        return []
    return _parse_bing_html(body, k)


def _clean_startpage_title(title) -> str:
    cleaned = _clean(title)
    return re.sub(r"^(?:[.#][^{]{1,80}\{[^{}]*\}\s*)+", "", cleaned).strip()


def _parse_startpage_html(body, limit=10) -> list:
    hits = []
    scrubbed_body = re.sub(
        r"<(?:style|script)\b[^>]*>.*?</(?:style|script)>",
        "",
        body,
        flags=re.DOTALL | re.I,
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
    try:
        body = _get(
            f"https://www.startpage.com/sp/search?{params}", timeout, headers=headers
        )
    except OSError:
        return []
    if _BLOCKED.search(body):
        _LOG.warning("startpage direct scraper blocked")
        return []
    return _parse_startpage_html(body, limit)


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
    try:
        body = _get(f"https://www.mojeek.com/search?{params}", timeout)
    except OSError:
        return []
    if _BLOCKED.search(body):
        _LOG.warning("mojeek direct scraper blocked")
        return []
    return _parse_mojeek_html(body, limit)


def norm_url(url) -> str:
    parts = urllib.parse.urlsplit(url.lower())
    path = parts.path.rstrip("/")
    query = urllib.parse.urlencode(
        sorted(urllib.parse.parse_qsl(parts.query, keep_blank_values=True))
    )
    return f"{parts.netloc}{path}?{query}" if query else f"{parts.netloc}{path}"


_norm_url = norm_url


def merge(result_lists, cap=20) -> list:
    by_url = {}
    for hits in result_lists:
        for hit in hits:
            key = norm_url(hit["url"])
            existing = by_url.get(key)
            if existing is None:
                by_url[key] = {**hit, "engines": [hit["engine"]]}
            else:
                existing["rank"] = min(existing["rank"], hit["rank"])
                if not existing.get("date") and hit.get("date"):
                    existing["date"] = hit["date"]
                if hit["engine"] not in existing["engines"]:
                    existing["engines"].append(hit["engine"])
    ordered = sorted(
        by_url.values(), key=lambda hit: (hit["rank"], -len(hit["engines"]))
    )
    return ordered[:cap]


def _build_tasks(query, config, k) -> dict:
    tasks = {}
    if config.get("searxng_url"):
        tasks["searxng"] = lambda: searxng(query, config["searxng_url"], k)
    if config.get("duckduckgo", True):
        tasks["duckduckgo"] = lambda: duckduckgo(query, k)
    if config.get("google", False):
        tasks["google"] = lambda: google(query, k, config=config)
    if config.get("bing", False):
        tasks["bing"] = lambda: bing(query, k)
    if config.get("startpage", False):
        tasks["startpage"] = lambda: startpage(query, k=k)
    if config.get("mojeek", False):
        tasks["mojeek"] = lambda: mojeek(query, k=k)
    return tasks


def search(query, config, k=10, cap=20) -> list:
    tasks = _build_tasks(query, config, k)
    if not tasks:
        return []
    lists = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, len(tasks))) as pool:
        futures = {pool.submit(fn): name for name, fn in tasks.items()}
        try:
            for future in concurrent.futures.as_completed(
                futures, timeout=_TIMEOUT + 2
            ):
                try:
                    lists.append(future.result())
                except Exception:
                    lists.append([])
        except concurrent.futures.TimeoutError:
            lists.extend(
                future.result()
                for future in futures
                if future.done() and not future.exception()
            )
    return merge(lists, cap)


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


def _demo_parsers() -> None:
    sample = '<a class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fok.com">Hit</a><a class="result__snippet" href="#">snip</a>'
    assert _parse_duckduckgo_html(sample)[0]["url"] == "https://ok.com", (
        "ddg html decode failed"
    )
    lite = '<table><tr><td><a href="https://lite.duckduckgo.com/lite/">DuckDuckGo</a></td></tr><tr><td><a href="//duckduckgo.com/l/?uddg=https%3A%2F%2Flite.com">Lite</a></td></tr><tr><td class="result-snippet">lite <b>snip</b></td></tr></table>'
    lite_hits = _parse_duckduckgo_lite(lite)
    assert len(lite_hits) == 1 and lite_hits[0]["snippet"] == "lite snip", (
        "ddg lite parse failed"
    )
    google_html = '<a href="/url?q=https%3A%2F%2Fg.com&sa=U"><h3>G</h3></a><div class="VwiC3b">gs</div>'
    assert _parse_google_html(google_html)[0]["url"] == "https://g.com", (
        "google html parse failed"
    )
    assert (
        _parse_google_json(
            '{"items":[{"title":"GJ","link":"https://gj.com","snippet":"gjs"}]}'
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
