#!/usr/bin/env python3
"""Benchmark deep_context_aware_search latency.

Run with real network access:
    python3 benchmark/deep_context_bench.py
"""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server"))
import mcp_server

QUERIES = [
    "climate change economic impact 2024",
    "transformer architecture self-attention",
    "quantum computing error correction",
]

FETCH_TOP_K_VALUES = [0, 5, 20]


def main():
    print("query                                          k    sec")
    for q in QUERIES:
        mcp_server.CONTEXT_MEMORY.clear()
        for k in FETCH_TOP_K_VALUES:
            t0 = time.perf_counter()
            mcp_server.deep_context_aware_search(q, fetch_top_k=k)
            print(f"{q[:44]:<45}{k:>2}{time.perf_counter()-t0:>7.2f}")


if __name__ == "__main__":
    main()
