#!/usr/bin/env python3
import concurrent.futures
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
_DDG_LITE_LINK = re.compile(r'<a[^>]+href="(?P<href>[^"]+)"[^>]*>(?P<title>.*?)</a>', re.DOTALL)
_DDG_LITE_SNIPPET = re.compile(r'<td[^>]+class="[^"]*result-snippet[^"]*"[^>]*>(?P<snippet>.*?)</td>', re.DOTALL)
_GOOGLE_LINK = re.compile(r'<a[^>]+href="(?P<href>[^"]+)"[^>]*>\s*<h3[^>]*>(?P<title>.*?)</h3>', re.DOTALL)
_GOOGLE_SNIPPET = re.compile(r'<div[^>]+class="[^"]*\bVwiC3b\b[^"]*"[^>]*>(?P<snippet>.*?)</div>', re.DOTALL)
_BING_BLOCK = re.compile(r'<li[^>]+class="[^"]*\bb_algo\b[^"]*"[^>]*>(?P<body>.*?)</li>', re.DOTALL)
_BING_LINK = re.compile(r'<h2[^>]*>\s*<a[^>]+href="(?P<href>[^"]+)"[^>]*>(?P<title>.*?)</a>', re.DOTALL)
_BING_CAPTION = re.compile(r'<div[^>]+class="[^"]*\bb_caption\b[^"]*"[^>]*>(?P<body>.*?)</div>', re.DOTALL)
_BING_SNIPPET = re.compile(r'<p[^>]*>(?P<snippet>.*?)</p>', re.DOTALL)
_BING_LEGACY_RESULT = re.compile(
    r'<li[^>]+class="[^"]*\bb_algo\b[^"]*"[^>]*>.*?'
    r'<h2[^>]*>\s*<a[^>]+href="(?P<href>[^"]+)"[^>]*>(?P<title>.*?)</a>.*?</h2>.*?'
    r'<p[^>]*>(?P<snippet>.*?)</p>',
    re.DOTALL,
)
_BLOCKED = re.compile(r"captcha|unusual traffic|verify you are human|automated queries|our systems have detected", re.I)
_LOG = logging.getLogger(__name__)


def result(title, url, snippet, engine, rank):
    return {"title": _clean(title), "url": url, "snippet": _clean(snippet), "engine": engine, "rank": rank}


def _clean(text):
    return html.unescape(re.sub(r"<[^>]+>", "", text or "")).strip()


def _get(url, timeout=_TIMEOUT, data=None, headers=None):
    request_headers = {"User-Agent": BROWSER_UA}
    if headers:
        request_headers.update(headers)
    request = urllib.request.Request(url, data=data, headers=request_headers)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", "replace")


def searxng(query, base, k=10, timeout=_TIMEOUT):
    params = urllib.parse.urlencode({"q": query, "format": "json"})
    try:
        payload = json.loads(_get(f"{base.rstrip('/')}/search?{params}", timeout))
    except (OSError, ValueError):
        return []
    hits = []
    for rank, row in enumerate(payload.get("results", [])[:k], 1):
        if row.get("url"):
            hits.append(result(row.get("title", ""), row["url"], row.get("content", ""), "searxng", rank))
    return hits


def _ddg_target(href):
    if "uddg=" in href:
        query = urllib.parse.urlparse(href).query
        target = urllib.parse.parse_qs(query).get("uddg", [None])[0]
        if target:
            return target
    return href if href.startswith("http") else "https:" + href


def _parse_duckduckgo_html(body, k=10):
    hits = []
    for rank, match in enumerate(_DDG_RESULT.finditer(body), 1):
        if rank > k:
            break
        hits.append(result(match["title"], _ddg_target(match["href"]), match["snippet"], "duckduckgo", rank))
    return hits


def _parse_duckduckgo_lite(body, k=10):
    hits = []
    matches = list(_DDG_LITE_LINK.finditer(body))
    for match in matches:
        href = html.unescape(match["href"])
        title = _clean(match["title"])
        if not title or "duckduckgo.com" in href and "uddg=" not in href:
            continue
        if title.lower() in {"next page", "previous page"}:
            continue
        next_start = next((other.start() for other in matches if other.start() > match.start()), len(body))
        snippet_match = _DDG_LITE_SNIPPET.search(body, match.end(), next_start)
        snippet = snippet_match["snippet"] if snippet_match else ""
        hits.append(result(title, _ddg_target(href), snippet, "duckduckgo", len(hits) + 1))
        if len(hits) >= k:
            break
    return hits


def duckduckgo(query, k=10, timeout=_TIMEOUT):
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


def _google_target(href):
    href = html.unescape(href)
    if href.startswith("/url?"):
        target = urllib.parse.parse_qs(urllib.parse.urlparse(href).query).get("q", [None])[0]
        if target:
            return target
    return href


def _parse_google_html(body, k=10):
    hits = []
    matches = list(_GOOGLE_LINK.finditer(body))
    for match in matches:
        target = _google_target(match["href"])
        if not target.startswith("http"):
            continue
        next_start = next((other.start() for other in matches if other.start() > match.start()), len(body))
        snippet_match = _GOOGLE_SNIPPET.search(body, match.end(), next_start)
        snippet = snippet_match["snippet"] if snippet_match else ""
        hits.append(result(match["title"], target, snippet, "google", len(hits) + 1))
        if len(hits) >= k:
            break
    return hits


def _parse_google_json(body, k=10):
    payload = json.loads(body)
    hits = []
    for item in payload.get("items", [])[:k]:
        if item.get("link"):
            hits.append(result(item.get("title", ""), item["link"], item.get("snippet", ""), "google", len(hits) + 1))
    return hits


def google(query, k=10, timeout=_TIMEOUT, config=None):
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
            return _parse_google_json(_get(f"https://customsearch.googleapis.com/customsearch/v1?{params}", timeout), k)
        except (OSError, ValueError, TypeError):
            pass
    params = urllib.parse.urlencode({"q": query, "num": k})
    try:
        body = _get(f"https://www.google.com/search?{params}", timeout, headers={"Cookie": "CONSENT=YES+"})
    except OSError:
        return []
    if _BLOCKED.search(body):
        _LOG.warning("google direct scraper blocked")
        return []
    return _parse_google_html(body, k)


def _parse_bing_html(body, k=10):
    hits = []
    for block_match in _BING_BLOCK.finditer(body):
        link_match = _BING_LINK.search(block_match["body"])
        caption_match = _BING_CAPTION.search(block_match["body"])
        snippet_match = _BING_SNIPPET.search(caption_match["body"]) if caption_match else None
        if link_match:
            snippet = snippet_match["snippet"] if snippet_match else ""
            hits.append(result(link_match["title"], html.unescape(link_match["href"]), snippet, "bing", len(hits) + 1))
        if len(hits) >= k:
            break
    if hits:
        return hits
    for rank, match in enumerate(_BING_LEGACY_RESULT.finditer(body), 1):
        if rank > k:
            break
        hits.append(result(match["title"], html.unescape(match["href"]), match["snippet"], "bing", rank))
    return hits


def bing(query, k=10, timeout=_TIMEOUT):
    params = urllib.parse.urlencode({"q": query})
    try:
        body = _get(f"https://www.bing.com/search?{params}", timeout)
    except OSError:
        return []
    if _BLOCKED.search(body):
        _LOG.warning("bing direct scraper blocked")
        return []
    return _parse_bing_html(body, k)


def _norm_url(url):
    parts = urllib.parse.urlsplit(url.lower())
    path = parts.path.rstrip("/")
    return f"{parts.netloc}{path}?{parts.query}" if parts.query else f"{parts.netloc}{path}"


def merge(result_lists, cap=20):
    by_url = {}
    for hits in result_lists:
        for hit in hits:
            key = _norm_url(hit["url"])
            existing = by_url.get(key)
            if existing is None:
                by_url[key] = {**hit, "engines": [hit["engine"]]}
            else:
                existing["rank"] = min(existing["rank"], hit["rank"])
                if hit["engine"] not in existing["engines"]:
                    existing["engines"].append(hit["engine"])
    ordered = sorted(by_url.values(), key=lambda hit: (hit["rank"], -len(hit["engines"])))
    return ordered[:cap]


def search(query, config, k=10, cap=20):
    tasks = {}
    if config.get("searxng_url"):
        tasks["searxng"] = lambda: searxng(query, config["searxng_url"], k)
    if config.get("duckduckgo", True):
        tasks["duckduckgo"] = lambda: duckduckgo(query, k)
    if config.get("google", True):
        tasks["google"] = lambda: google(query, k, config=config)
    if config.get("bing", True):
        tasks["bing"] = lambda: bing(query, k)
    if not tasks:
        return []
    lists = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, len(tasks))) as pool:
        futures = {pool.submit(fn): name for name, fn in tasks.items()}
        for future in concurrent.futures.as_completed(futures, timeout=_TIMEOUT + 2):
            try:
                lists.append(future.result())
            except Exception:
                lists.append([])
    return merge(lists, cap)


def demo():
    primary = [result("A", "https://x.com/p", "sa", "searxng", 1), result("B", "https://y.com", "sb", "searxng", 2)]
    secondary = [result("A2", "https://X.com/p/", "sb2", "duckduckgo", 3)]
    merged = merge([primary, secondary])
    assert len(merged) == 2, merged
    top = merged[0]
    assert top["rank"] == 1 and set(top["engines"]) == {"searxng", "duckduckgo"}, top
    sample = '<a class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fok.com">Hit</a>' \
             '<a class="result__snippet" href="#">snip</a>'
    assert _parse_duckduckgo_html(sample)[0]["url"] == "https://ok.com", "ddg html decode failed"
    lite = (
        '<table><tr><td><a href="//duckduckgo.com/l/?uddg=https%3A%2F%2Flite.com">Lite</a></td></tr>'
        '<tr><td class="result-snippet">lite <b>snip</b></td></tr></table>'
    )
    assert _parse_duckduckgo_lite(lite)[0]["snippet"] == "lite snip", "ddg lite parse failed"
    google_html = '<a href="/url?q=https%3A%2F%2Fg.com&sa=U"><h3>G</h3></a><div class="VwiC3b">gs</div>'
    assert _parse_google_html(google_html)[0]["url"] == "https://g.com", "google html parse failed"
    google_json = '{"items":[{"title":"GJ","link":"https://gj.com","snippet":"gjs"}]}'
    assert _parse_google_json(google_json)[0]["title"] == "GJ", "google json parse failed"
    bing_html = '<li class="b_algo"><h2><a href="https://b.com">B</a></h2><div class="b_caption"><p>bs</p></div></li>'
    assert _parse_bing_html(bing_html)[0]["snippet"] == "bs", "bing parse failed"
    print("demo ok")


if __name__ == "__main__":
    demo()
