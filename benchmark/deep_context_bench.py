#!/usr/bin/env python3
"""Time deep_context_aware_search at each fetch_top_k, needs real network."""
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
        for k in FETCH_TOP_K_VALUES:
            mcp_server.CONTEXT_MEMORY.clear()
            t0 = time.perf_counter()
            mcp_server.deep_context_aware_search(q, fetch_top_k=k)
            print(f"{q[:44]:<45}{k:>2}{time.perf_counter()-t0:>7.2f}")


if __name__ == "__main__":
    main()
