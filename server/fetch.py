import codecs
import re
import urllib.parse
import urllib.request
from html.parser import HTMLParser

_UA = "Mozilla/5.0 (compatible knowledge-based-search/0.1)"
_BLOCK_TAGS = {"div", "main", "article", "section"}
_BREAK_TAGS = {"br", "p", "li", "h1", "h2", "h3", "h4", "h5", "h6"}
_SKIP_TAGS = {"aside", "footer", "form", "header", "nav", "noscript", "script", "style", "svg", "template"}
_USEFUL_TAGS = {"p", "li"}


class _TextParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks = []
        self.current = []
        self.link_depth = 0
        self.skip = []
        self.useful_depth = 0
        self.whole_page = {"tag": "body", "parts": [], "chars": 0, "link_chars": 0, "useful_chars": 0}

    def handle_starttag(self, tag, attrs):
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
            self.current.append({"tag": tag, "parts": [], "chars": 0, "link_chars": 0, "useful_chars": 0})
        if tag in _USEFUL_TAGS:
            self.useful_depth += 1
        if tag in _BREAK_TAGS:
            self._append("\n\n")

    def handle_endtag(self, tag):
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
            for index in range(len(self.current) - 1, -1, -1):
                if self.current[index]["tag"] == tag:
                    self.blocks.append(self.current.pop(index))
                    break

    def handle_data(self, data):
        if self.skip:
            return
        text = data.strip()
        if text:
            self._append(text)

    def best_text(self):
        viable_blocks = [block for block in self.blocks + self.current if _score(block) >= 0]
        best = max(viable_blocks, key=_score) if viable_blocks else self.whole_page
        return _clean_text(" ".join(best["parts"]))

    def _append(self, text):
        for block in self.current + [self.whole_page]:
            block["parts"].append(text)
            if text.strip():
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
    match = re.search(r"charset\s*=\s*['\"]?([^;'\"\s]+)", content_type or "", re.I)
    if not match:
        return "utf-8"
    charset = match.group(1)
    try:
        codecs.lookup(charset)
    except LookupError:
        return "utf-8"
    return charset


def fetch_clean(url, max_chars):
    if urllib.parse.urlsplit(url).path.lower().endswith(".pdf"):
        return ""
    request = urllib.request.Request(url, headers={"User-Agent": _UA})
    with urllib.request.urlopen(request, timeout=10) as response:
        header_reader = getattr(response, "getheader", lambda name, default=None: default)
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
