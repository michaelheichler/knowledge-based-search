"""Direct web provider adapters and parsers with lazy shared-helper access."""

import html
import json
import re
import urllib.parse

import engines as _engines

_TIMEOUT = 12.0

def searxng(query, base, k=10, timeout=_TIMEOUT) -> list:
    """Query one SearXNG provider."""
    params = urllib.parse.urlencode({"q": query, "format": "json"})
    payload = json.loads(_engines._get(f"{base.rstrip('/')}/search?{params}", timeout))
    hits = []
    for rank, row in enumerate(payload.get("results", [])[:k], 1):
        if row.get("url"):
            hits.append(
                _engines.result(
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
    payload = json.loads(_engines._get(f"https://mwmbl.org/api/v1/search/?{params}", timeout))
    hits = []
    for rank, row in enumerate(payload[:k], 1):
        if not row.get("url"):
            continue
        title = "".join(segment.get("value", "") for segment in row.get("title", []))
        snippet = "".join(
            segment.get("value", "") for segment in row.get("extract", [])
        )
        hits.append(_engines.result(title, row["url"], snippet, "mwmbl", rank))
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
    payload = json.loads(_engines._get(f"https://en.wikipedia.org/w/api.php?{params}", timeout))
    rows = payload.get("query", {}).get("search", [])[:k]
    return [
        _engines.result(
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


def tavily(query, k=10, timeout=_TIMEOUT, config: dict | None = None) -> list:
    """Query Tavily with the configured free API key."""
    if config is None or not config.get("tavily_api_key"):
        raise ValueError("tavily_api_key is required")
    request_body = json.dumps(
        {"api_key": config["tavily_api_key"], "query": query, "max_results": k}
    ).encode("utf-8")
    payload = json.loads(
        _engines._get(
            "https://api.tavily.com/search",
            timeout,
            data=request_body,
            headers={"Content-Type": "application/json"},
        )
    )
    return [
        _engines.result(
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
    for rank, match in enumerate(_engines._DDG_RESULT.finditer(body), 1):
        if rank > k:
            break
        hits.append(
            _engines.result(
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
    matches = list(_engines._DDG_LITE_LINK.finditer(body))
    for match in matches:
        href = html.unescape(match["href"])
        title = _engines._clean(match["title"])
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
        snippet_match = _engines._DDG_LITE_SNIPPET.search(body, match.end(), next_start)
        snippet = snippet_match["snippet"] if snippet_match else ""
        hits.append(_engines.result(title, target, snippet, "duckduckgo", len(hits) + 1))
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
        body = _engines._get(
            "https://lite.duckduckgo.com/lite/", timeout, data=form, headers=headers
        )
        hits = _parse_duckduckgo_lite(body, k)
        if hits:
            return hits
        _engines._raise_if_blocked(body, "duckduckgo", hits)
    except _engines.ProviderBlocked:
        lite_blocked = True
    except OSError:
        pass
    body = _engines._get(f"https://html.duckduckgo.com/html/?{params}", timeout)
    hits = _parse_duckduckgo_html(body, k)
    _engines._raise_if_blocked(body, "duckduckgo", hits)
    if lite_blocked and not hits:
        raise _engines.ProviderBlocked("duckduckgo")
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
    matches = list(_engines._GOOGLE_LINK.finditer(body))
    for match in matches:
        target = _google_target(match["href"])
        if not target.startswith("http"):
            continue
        next_start = next(
            (other.start() for other in matches if other.start() > match.start()),
            len(body),
        )
        snippet_match = _engines._GOOGLE_SNIPPET.search(body, match.end(), next_start)
        snippet = snippet_match["snippet"] if snippet_match else ""
        hits.append(_engines.result(match["title"], target, snippet, "google", len(hits) + 1))
        if len(hits) >= k:
            break
    return hits


def _parse_google_json(payload, k=10) -> list:
    hits = []
    for item in payload.get("items", [])[:k]:
        if item.get("link"):
            hits.append(
                _engines.result(
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
    payload = _engines._get(
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
    body = _engines._get(
        f"https://www.google.com/search?{params}",
        timeout,
        headers={"Cookie": "CONSENT=YES+"},
    )
    hits = _parse_google_html(body, k)
    _engines._raise_if_blocked(body, "google", hits)
    return hits


def _parse_bing_html(body, k=10) -> list:
    hits = []
    for block_match in _engines._BING_BLOCK.finditer(body):
        link_match = _engines._BING_LINK.search(block_match["body"])
        caption_match = _engines._BING_CAPTION.search(block_match["body"])
        snippet_match = (
            _engines._BING_SNIPPET.search(caption_match["body"]) if caption_match else None
        )
        if link_match:
            snippet = snippet_match["snippet"] if snippet_match else ""
            hits.append(
                _engines.result(
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
    for rank, match in enumerate(_engines._BING_LEGACY_RESULT.finditer(body), 1):
        if rank > k:
            break
        hits.append(
            _engines.result(
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
    body = _engines._get(f"https://www.bing.com/search?{params}", timeout)
    hits = _parse_bing_html(body, k)
    _engines._raise_if_blocked(body, "bing", hits)
    return hits


def _clean_startpage_title(title) -> str:
    cleaned = _engines._clean(title)
    return re.sub(r"^(?:[.#][^{]{1,80}\{[^{}]*\}\s*)+", "", cleaned).strip()


def _parse_startpage_html(body, limit=10) -> list:
    hits = []
    scrubbed_body = re.sub(
        r"<(?:style|script)\b[^>]*>.*?</(?:style|script)>",
        "",
        body,
        flags=re.DOTALL | re.IGNORECASE,
    )
    for match in _engines._STARTPAGE_LINK.finditer(scrubbed_body):
        attrs = match["attrs"]
        class_name = _engines._attr(attrs, "class")
        if "result" not in class_name and "w-gl__result-title" not in class_name:
            continue
        title = _clean_startpage_title(match["title"])
        href = _engines._attr(attrs, "href")
        if not title or not href:
            continue
        snippet_match = _engines._STARTPAGE_SNIPPET.search(match["tail"])
        snippet = snippet_match["snippet"] if snippet_match else ""
        url = _engines._redirect_target(href, "https://www.startpage.com", ("url", "u"))
        if url.startswith("http"):
            hits.append(_engines.result(title, url, snippet, "startpage", len(hits) + 1))
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
    body = _engines._get(
        f"https://www.startpage.com/sp/search?{params}", timeout, headers=headers
    )
    hits = _parse_startpage_html(body, limit)
    _engines._raise_if_blocked(body, "startpage", hits)
    return hits


def _parse_mojeek_html(body, limit=10) -> list:
    hits = []
    for match in _engines._MOJEEK_RESULT.finditer(body):
        href = _engines._attr(match["attrs"], "href")
        title = _engines._clean(match["title"])
        if not href or not title:
            continue
        snippet_match = _engines._MOJEEK_SNIPPET.search(match["tail"])
        snippet = snippet_match["snippet"] if snippet_match else ""
        url = _engines._absolute_url(href, "https://www.mojeek.com")
        if url.startswith("http"):
            hits.append(_engines.result(title, url, snippet, "mojeek", len(hits) + 1))
        if len(hits) >= limit:
            break
    return hits


def mojeek(query, timeout=_TIMEOUT, **options) -> list:
    limit = options.get("k", 10)
    params = urllib.parse.urlencode({"q": query})
    body = _engines._get(f"https://www.mojeek.com/search?{params}", timeout)
    hits = _parse_mojeek_html(body, limit)
    _engines._raise_if_blocked(body, "mojeek", hits)
    return hits
