"""Fetch and extract public web pages with SSRF protection."""

import codecs
import ipaddress
import os
import re
import socket
import urllib.parse
import urllib.request
from html.parser import HTMLParser

_UA = "Mozilla/5.0 (compatible knowledge-based-search/0.1)"


class BlockedFetchError(ValueError):
    """Signal that URL policy blocked a fetch before connection."""


_BLOCK_TAGS = {"div", "main", "article", "section"}
_BREAK_TAGS = {"br", "p", "li", "h1", "h2", "h3", "h4", "h5", "h6"}
_SKIP_TAGS = {
    "aside",
    "footer",
    "form",
    "header",
    "nav",
    "noscript",
    "script",
    "style",
    "svg",
    "template",
}
_USEFUL_TAGS = {"p", "li"}


class _TextParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks = []
        self.current = []
        self.link_depth = 0
        self.skip = []
        self.useful_depth = 0
        self.whole_page = {
            "tag": "body",
            "parts": [],
            "chars": 0,
            "link_chars": 0,
            "useful_chars": 0,
        }

    def handle_starttag(self, tag, attrs) -> None:
        tag = tag.lower()
        if self.skip:
            if tag in _SKIP_TAGS:
                self.skip.append(tag)
            return
        if tag in _SKIP_TAGS:
            self.skip.append(tag)
            return
        if tag == "a":
            self.link_depth += 1
        if tag in _BLOCK_TAGS:
            self.current.append(
                {
                    "tag": tag,
                    "parts": [],
                    "chars": 0,
                    "link_chars": 0,
                    "useful_chars": 0,
                }
            )
        if tag in _USEFUL_TAGS:
            self.useful_depth += 1
        if tag in _BREAK_TAGS:
            self._append("\n\n")

    def handle_endtag(self, tag) -> None:
        tag = tag.lower()
        if self.skip:
            if self.skip[-1] == tag:
                self.skip.pop()
            return
        if tag in _BREAK_TAGS:
            self._append("\n\n")
        if tag in _USEFUL_TAGS and self.useful_depth:
            self.useful_depth -= 1
        if tag == "a" and self.link_depth:
            self.link_depth -= 1
        if tag in _BLOCK_TAGS:
            self._close_block(tag)

    def _close_block(self, tag) -> None:
        for index in range(len(self.current) - 1, -1, -1):
            if self.current[index]["tag"] != tag:
                continue
            self.blocks.append(self.current.pop(index))
            return

    def handle_data(self, data) -> None:
        if self.skip:
            return
        text = data.strip()
        if text:
            self._append(text)

    def best_text(self) -> str:
        viable_blocks = [
            block for block in self.blocks + self.current if _score(block) >= 0
        ]
        best = max(viable_blocks, key=_score) if viable_blocks else self.whole_page
        if best["chars"] and best["link_chars"] * 2 >= best["chars"]:
            return ""
        return _clean_text(" ".join(best["parts"]))

    def _append(self, text) -> None:
        for block in self.current + [self.whole_page]:
            self._append_to_block(block, text)

    def _append_to_block(self, block, text) -> None:
        """Counters share one text span because mixed spans would corrupt density scoring."""
        block["parts"].append(text)
        if not text.strip():
            return
        size = len(text)
        block["chars"] += size
        if self.link_depth:
            block["link_chars"] += size
        if self.useful_depth:
            block["useful_chars"] += size


def _score(block):
    chars = block["chars"]
    if not chars or block["link_chars"] * 2 >= chars:
        return -1
    priority = 1_000_000 if block["tag"] in {"article", "main"} else 0
    return priority + block["useful_chars"] * 2 + chars


def _clean_text(text):
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r" *\n+ *", "\n\n", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _charset(content_type):
    match = re.search(r"charset\s*=\s*['\"]?([^;'\"\s]+)", content_type or "", re.IGNORECASE)
    if not match:
        return "utf-8"
    charset = match.group(1)
    try:
        codecs.lookup(charset)
    except LookupError:
        return "utf-8"
    return charset


def _allow_private() -> bool:
    """The bypass requires explicit opt in because fetched URLs may come from untrusted pages."""
    return os.environ.get("KBS_ALLOW_PRIVATE") == "1"


def _forbidden_address(value: str) -> bool:
    """These ranges stay blocked because public fetches must never reach local networks."""
    address = ipaddress.ip_address(value)
    return any(
        (
            address.is_loopback,
            address.is_link_local,
            address.is_private,
            address.is_multicast,
            address.is_reserved,
            address.is_unspecified,
        )
    )


def _validate_url(url: str) -> None:
    """Resolution precedes connection because request forgery must be stopped before network I/O."""
    parts = urllib.parse.urlsplit(url)
    if parts.scheme.lower() not in {"http", "https"}:
        raise BlockedFetchError("only http and https URLs are allowed")
    if not parts.hostname:
        raise BlockedFetchError("URL must include a host")
    if _allow_private():
        return
    port = parts.port or (443 if parts.scheme.lower() == "https" else 80)
    addresses = socket.getaddrinfo(parts.hostname, port, type=socket.SOCK_STREAM)
    if not addresses:
        raise OSError(f"host did not resolve: {parts.hostname}")
    if any(_forbidden_address(item[4][0]) for item in addresses):
        raise BlockedFetchError("private or special-use network addresses are not allowed")


class _SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    """A custom handler is required because urllib follows location headers automatically."""

    def redirect_request(self, req, fp, code, msg, headers, newurl) -> object:
        _validate_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _open(request, timeout):
    """A dedicated opener is required because global urllib behavior would bypass this policy."""
    return urllib.request.build_opener(_SafeRedirectHandler()).open(
        request, timeout=timeout
    )


def fetch_clean(url, max_chars) -> str:
    """Fetch one public HTML page and return its useful text."""
    _validate_url(url)
    if urllib.parse.urlsplit(url).path.lower().endswith(".pdf"):
        return ""
    request = urllib.request.Request(url, headers={"User-Agent": _UA})
    with _open(request, timeout=10) as response:
        final_url = getattr(response, "geturl", lambda: url)()
        _validate_url(final_url)
        header_reader = getattr(
            response, "getheader", lambda name, default=None: default
        )
        content_type = header_reader("Content-Type", "text/html")
        if "html" not in (content_type or "").lower():
            return ""
        body = response.read(min(max_chars * 4, 2_000_000))
        if body.startswith(b"%PDF-"):
            return ""
        body = body.decode(_charset(content_type), "replace")
    parser = _TextParser()
    parser.feed(body)
    return parser.best_text()[:max_chars]
