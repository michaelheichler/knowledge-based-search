"""Keyless scientific-literature provider adapters, split out to keep engines.py under the size cap."""

import json
import urllib.parse
import xml.etree.ElementTree as ET  # ponytail: trusted first-party API, add defusedxml if that changes

import engines

_ARXIV_NS = "{http://www.w3.org/2005/Atom}"


def _arxiv_hit(entry, rank) -> dict | None:
    entry_id = entry.findtext(f"{_ARXIV_NS}id") or ""
    title = " ".join((entry.findtext(f"{_ARXIV_NS}title") or "").split())
    if not entry_id or not title:
        return None
    summary = " ".join((entry.findtext(f"{_ARXIV_NS}summary") or "").split())
    hit = engines.result(title, entry_id, summary, "arxiv", rank)
    hit["date"] = (entry.findtext(f"{_ARXIV_NS}published") or "")[:10]
    return hit


def arxiv(query, k=10, timeout=engines._TIMEOUT) -> list:
    """Query the keyless arXiv API."""
    params = urllib.parse.urlencode(
        {"search_query": f"all:{query}", "start": 0, "max_results": k}
    )
    body = engines._api_get(
        f"https://export.arxiv.org/api/query?{params}",
        "arxiv",
        timeout,
        headers={"User-Agent": engines._SCIENCE_UA},
    )
    hits = []
    for entry in ET.fromstring(body).findall(f"{_ARXIV_NS}entry"):
        if len(hits) >= k:
            break
        hit = _arxiv_hit(entry, len(hits) + 1)
        if hit:
            hits.append(hit)
    return hits


def _parse_pubmed_date(text) -> str:
    parts = (text or "").split()
    if not parts:
        return ""
    year = parts[0]
    month = engines._MONTHS.get(parts[1].lower()) if len(parts) > 1 else None
    if not month:
        return ""
    day = parts[2] if len(parts) > 2 else "1"
    return engines._safe_iso_date(year, str(month), day)


def _pubmed_fetch_ids(query, k, timeout) -> list:
    params = urllib.parse.urlencode(
        {"db": "pubmed", "term": query, "retmode": "json", "retmax": k}
    )
    body = engines._api_get(
        f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?{params}",
        "pubmed",
        timeout,
        headers={"User-Agent": engines._SCIENCE_UA},
    )
    return json.loads(body).get("esearchresult", {}).get("idlist", [])


def _pubmed_fetch_summaries(idlist, timeout) -> dict:
    params = urllib.parse.urlencode(
        {"db": "pubmed", "id": ",".join(idlist), "retmode": "json"}
    )
    body = engines._api_get(
        f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?{params}",
        "pubmed",
        timeout,
        headers={"User-Agent": engines._SCIENCE_UA},
    )
    return json.loads(body).get("result", {})


def _pubmed_hit(pmid, row, rank) -> dict | None:
    if not row or not row.get("title"):
        return None
    snippet = " ".join(part for part in (row.get("source"), row.get("pubdate")) if part)
    hit = engines.result(
        row["title"], f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/", snippet, "pubmed", rank
    )
    hit["date"] = _parse_pubmed_date(row.get("pubdate", ""))
    return hit


def pubmed(query, k=10, timeout=engines._TIMEOUT) -> list:
    """Query PubMed via NCBI E-utilities. esearch for PMIDs, esummary for metadata."""
    idlist = _pubmed_fetch_ids(query, k, timeout)
    if not idlist:
        return []
    summary = _pubmed_fetch_summaries(idlist, timeout)
    hits = []
    for pmid in idlist:
        hit = _pubmed_hit(pmid, summary.get(pmid), len(hits) + 1)
        if hit:
            hits.append(hit)
    return hits


def _semanticscholar_hit(row, rank) -> dict | None:
    if not row.get("title") or not row.get("url"):
        return None
    year = row.get("year")
    authors = ", ".join(
        author.get("name", "") for author in row.get("authors", []) if author.get("name")
    )
    fallback = " - ".join(part for part in (authors, str(year) if year else "") if part)
    hit = engines.result(
        row["title"], row["url"], row.get("abstract") or fallback, "semanticscholar", rank
    )
    hit["date"] = engines._safe_iso_date(str(year), "1", "1") if year else ""
    hit["citation_count"] = int(row.get("citationCount") or 0)
    return hit


def semanticscholar(query, k=10, timeout=engines._TIMEOUT) -> list:
    """Query the keyless Semantic Scholar Graph API."""
    params = urllib.parse.urlencode(
        {"query": query, "limit": k, "fields": "title,abstract,year,citationCount,url,authors"}
    )
    body = engines._api_get(
        f"https://api.semanticscholar.org/graph/v1/paper/search?{params}",
        "semanticscholar",
        timeout,
        headers={"User-Agent": engines._SCIENCE_UA},
    )
    hits = []
    for row in json.loads(body).get("data", []):
        if len(hits) >= k:
            break
        hit = _semanticscholar_hit(row, len(hits) + 1)
        if hit:
            hits.append(hit)
    return hits


def _crossref_date(row) -> str:
    for field in ("published-print", "published-online", "issued", "created"):
        candidate = row.get(field, {}).get("date-parts")
        if candidate and candidate[0]:
            parts = candidate[0]
            year = parts[0]
            month = parts[1] if len(parts) > 1 else 1
            day = parts[2] if len(parts) > 2 else 1
            return engines._safe_iso_date(str(year), str(month), str(day))
    return ""


def _crossref_hit(row, rank) -> dict | None:
    titles = row.get("title") or []
    if not titles or not row.get("URL"):
        return None
    container = ", ".join(row.get("container-title") or [])
    authors = ", ".join(
        author.get("family", "") for author in row.get("author", []) if author.get("family")
    )
    snippet = " - ".join(part for part in (container, authors) if part)
    hit = engines.result(titles[0], row["URL"], snippet, "crossref", rank)
    hit["date"] = _crossref_date(row)
    hit["citation_count"] = int(row.get("is-referenced-by-count") or 0)
    return hit


def crossref(query, k=10, timeout=engines._TIMEOUT, config=None) -> list:
    """Query the keyless CrossRef works API. mailto enrolls in the polite pool, never auth."""
    params = {"query": query, "rows": k}
    mailto = (config or {}).get("crossref_mailto")
    if mailto:
        params["mailto"] = mailto
    body = engines._api_get(
        f"https://api.crossref.org/works?{urllib.parse.urlencode(params)}",
        "crossref",
        timeout,
        headers={"User-Agent": engines._SCIENCE_UA},
    )
    hits = []
    for row in json.loads(body).get("message", {}).get("items", []):
        if len(hits) >= k:
            break
        hit = _crossref_hit(row, len(hits) + 1)
        if hit:
            hits.append(hit)
    return hits
