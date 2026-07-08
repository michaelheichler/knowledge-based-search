#!/usr/bin/env python3
# ruff: noqa
"""Time deep_context_aware_search at each fetch_top_k, needs real network."""

import importlib
import os
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))
search_core = importlib.import_module("search_core")
state = importlib.import_module("state")

QUERIES = [
    "climate change economic impact 2024",
    "transformer architecture self-attention",
    "quantum computing error correction",
]

FETCH_TOP_K_VALUES = [0, 5, 20]


def main():
    print("query                                          k    sec")
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["KBS_STATE_FILE"] = str(Path(tmp) / "state.json")
        for query in QUERIES:
            for fetch_top_k in FETCH_TOP_K_VALUES:
                state.clear_session()
                start = time.perf_counter()
                search_core.deep_context_aware_search(query, {}, fetch_top_k=fetch_top_k)
                elapsed = time.perf_counter() - start
                print(f"{query[:44]:<45}{fetch_top_k:>2}{elapsed:>7.2f}")


if __name__ == "__main__":
    main()
