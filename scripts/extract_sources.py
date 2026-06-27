#!/usr/bin/env python3
"""Extract the source books to per-chapter text units plus a manifest for the summary workflow."""
import json
import os
import re
import subprocess
import sys
import zipfile
from html.parser import HTMLParser

OUT_ROOT = os.environ.get("KBS_BUILD_DIR", "/tmp/kbs_build")

SOURCES = [
    {
        "slug": "osint-techniques",
        "path": "/Users/michael/Downloads/OSINT Techniques (Michael Bazzell, Jason Edison) (z-library.sk, 1lib.sk, z-lib.sk).epub",
        "kind": "epub",
    },
    {
        "slug": "osint-resources",
        "path": "/Users/michael/Downloads/Open Source Intelligence Techniques Resources for Searching and Analyzing Online Information (Michael Bazzell) (z-library.sk, 1lib.sk, z-lib.sk).pdf",
        "kind": "pdf",
    },
    {
        "slug": "digital-research-methods",
        "path": "/Users/michael/Downloads/Handbook of Digital and Computational Research Methods In the Social Sciences and Humanities (Anders Koed Madsen, Anders Kristian Munk) (z-library.sk, 1lib.sk, z-lib.sk).pdf",
        "kind": "pdf",
    },
]

_MIN_UNIT_CHARS = 1500
_FIXED_UNIT_CHARS = 30000
_OUTLINE_KEEP = re.compile(r"^\s*(chapter\s+\d+|part\s+[ivxlc\d]+)\b", re.IGNORECASE)


class _Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self._skip = 0
        self._heading = None
        self.title = None
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self._skip += 1
        elif tag in ("h1", "h2", "h3") and self.title is None:
            self._heading = tag

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self._skip:
            self._skip -= 1
        elif tag == self._heading:
            self._heading = None

    def handle_data(self, data):
        if self._skip or not data.strip():
            return
        if self._heading and self.title is None:
            self.title = data.strip()[:120]
        self.parts.append(data)


def _parse_html(html):
    parser = _Text()
    parser.feed(html)
    text = re.sub(r"\n{3,}", "\n\n", "\n".join(parser.parts))
    return parser.title, text


def _epub_units(path):
    units = []
    with zipfile.ZipFile(path) as zf:
        docs = sorted(n for n in zf.namelist() if n.lower().endswith((".xhtml", ".html", ".htm")))
        for name in docs:
            title, text = _parse_html(zf.read(name).decode("utf-8", "replace"))
            text = text.strip()
            if len(text) >= _MIN_UNIT_CHARS:
                units.append((title or name, text))
    return units


def _pdf_pages(path):
    try:
        out = subprocess.run(["pdftotext", "-q", path, "-"], capture_output=True, timeout=300)
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.decode("utf-8", "replace").split("\f")
    except (OSError, subprocess.SubprocessError):
        pass
    from pypdf import PdfReader

    return [page.extract_text() or "" for page in PdfReader(path).pages]


def _outline_spans(path):
    """Return [(title, start_page)] for chapter and part bookmarks, or [] when absent."""
    from pypdf import PdfReader

    reader = PdfReader(path)

    def walk(items):
        found = []
        for item in items:
            if isinstance(item, list):
                found += walk(item)
                continue
            title = getattr(item, "title", "") or ""
            if _OUTLINE_KEEP.match(title):
                found.append((title.strip()[:120], reader.get_destination_page_number(item)))
        return found

    try:
        return walk(reader.outline)
    except Exception:
        return []


def _fixed_units(text):
    chunks = [text[i : i + _FIXED_UNIT_CHARS] for i in range(0, len(text), _FIXED_UNIT_CHARS)]
    return [(f"section {i + 1}", chunk.strip()) for i, chunk in enumerate(chunks) if chunk.strip()]


def _pdf_units(path):
    pages = _pdf_pages(path)
    spans = _outline_spans(path)
    if len(spans) < 3:
        return _fixed_units("\n".join(pages))
    units = []
    for idx, (title, start) in enumerate(spans):
        end = spans[idx + 1][1] if idx + 1 < len(spans) else len(pages)
        body = "\n".join(pages[start:end]).strip()
        if len(body) >= _MIN_UNIT_CHARS:
            units.append((title, body))
    return units


def _extract_one(source):
    units = _epub_units(source["path"]) if source["kind"] == "epub" else _pdf_units(source["path"])
    out_dir = os.path.join(OUT_ROOT, source["slug"])
    os.makedirs(out_dir, exist_ok=True)
    records = []
    for idx, (title, body) in enumerate(units, 1):
        unit_id = f"ch{idx:02d}"
        unit_path = os.path.join(out_dir, f"{unit_id}.txt")
        with open(unit_path, "w", encoding="utf-8") as fh:
            fh.write(body)
        records.append({"id": unit_id, "title": title, "path": unit_path, "chars": len(body)})
    return records


def run():
    manifest = {}
    for source in SOURCES:
        if not os.path.exists(source["path"]):
            print(f"MISSING source: {source['path']}", file=sys.stderr)
            continue
        records = _extract_one(source)
        manifest[source["slug"]] = records
        print(f"{source['slug']}: {len(records)} units")
    os.makedirs(OUT_ROOT, exist_ok=True)
    manifest_path = os.path.join(OUT_ROOT, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
    print(f"manifest: {manifest_path}")
    return manifest


def demo():
    title, text = _parse_html("<h1>Email Search</h1><p>" + "body. " * 400 + "</p>")
    assert title == "Email Search", title
    assert "body." in text
    fixed = _fixed_units("x" * (_FIXED_UNIT_CHARS * 2 + 10))
    assert len(fixed) == 3, len(fixed)
    print("demo ok")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo()
    else:
        run()
