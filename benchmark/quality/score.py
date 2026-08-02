#!/usr/bin/env python3
"""Objective per-variant quality metrics, no LLM and no human."""
import json
import os
from urllib.parse import urlsplit

_KEYS = ("result_count", "unique_domain_ratio", "date_present_ratio", "mean_relevance", "top1_relevance", "engine_diversity")


def _domain(url):
    return urlsplit(url).netloc.lower()


def unique_domain_ratio(results):
    if not results:
        return 0.0
    return round(len({_domain(r.get("url", "")) for r in results}) / len(results), 3)


def date_present_ratio(results):
    if not results:
        return 0.0
    return round(sum(1 for r in results if r.get("date")) / len(results), 3)


def recency_hit(results, top=5):
    head = results[:top]
    if not head:
        return 0.0
    return round(sum(1 for r in head if str(r.get("date", ""))[:4] in ("2025", "2026")) / len(head), 3)


def mean_relevance(results):
    if not results:
        return 0.0
    return round(sum(float(r.get("relevance", 0.0)) for r in results) / len(results), 3)


def top1_relevance(results):
    return round(float(results[0].get("relevance", 0.0)), 3) if results else 0.0


def engine_diversity(results):
    found = set()
    for r in results:
        found.update(r.get("engines") or [])
    return len(found)


def score_query(results, category):
    metrics = {
        "result_count": len(results),
        "unique_domain_ratio": unique_domain_ratio(results),
        "date_present_ratio": date_present_ratio(results),
        "mean_relevance": mean_relevance(results),
        "top1_relevance": top1_relevance(results),
        "engine_diversity": engine_diversity(results),
    }
    if category == "recency":
        metrics["recency_hit"] = recency_hit(results)
    return metrics


def _aggregate(results, categories):
    rows = [score_query(r, categories.get(qid, "")) for qid, r in results.items()]
    summary = {k: round(sum(row.get(k, 0) for row in rows) / max(len(rows), 1), 3) for k in _KEYS}
    recency = [row["recency_hit"] for row in rows if "recency_hit" in row]
    summary["recency_hit"] = round(sum(recency) / max(len(recency), 1), 3) if recency else 0.0
    return summary


def _load_runs(runs_dir):
    runs = {}
    for name in sorted(os.listdir(runs_dir)):
        if name.endswith(".json"):
            with open(os.path.join(runs_dir, name), encoding="utf-8") as handle:
                payload = json.load(handle)
            runs[payload["variant"]] = payload["results"]
    return runs


def _print_table(summaries):
    cols = _KEYS + ("recency_hit",)
    print("variant".ljust(14) + "".join(c[:11].rjust(13) for c in cols))
    for name, summary in summaries.items():
        print(name.ljust(14) + "".join(f"{summary.get(c, 0):>13}" for c in cols))


def main():
    here = os.path.dirname(__file__)
    with open(os.path.join(here, "queries.json"), encoding="utf-8") as handle:
        queries = json.load(handle)["queries"]
    categories = {q["id"]: q["category"] for q in queries}
    runs = _load_runs(os.path.join(here, "runs"))
    summaries = {name: _aggregate(results, categories) for name, results in runs.items()}
    _print_table(summaries)


if __name__ == "__main__":
    main()
