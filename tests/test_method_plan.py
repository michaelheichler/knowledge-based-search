#!/usr/bin/env python3
# ruff: noqa
"""Standalone checks for the kbs plan method index."""

import os
import shlex
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))
import method_index  # type: ignore[import-not-found]

_REPO_ROOT = Path(__file__).resolve().parents[1]
_REF_DIR = _REPO_ROOT / "skills" / "knowledge-based-search" / "references"

_EXPECTED_METHOD_WORDS = [
    "fact-check",
    "fact check",
    "verify a claim",
    "osint",
    "how to investigate",
    "how to research",
    "source evaluation",
    "evaluate evidence",
    "trace a username",
    "trace an email",
    "domain lookup",
    "who is",
    "geolocate",
    "dorking",
    "investigation method",
    "tradecraft",
]


class MethodPlanTests(unittest.TestCase):
    def test_method_table_paths_exist(self):
        for route in method_index._ROUTES:
            for ref in route["references"]:
                full = _REF_DIR / ref
                self.assertTrue(
                    full.exists(),
                    f"Reference path does not exist: {ref}",
                )

    def test_method_words_are_covered(self):
        for word in _EXPECTED_METHOD_WORDS:
            result = method_index.plan_search(word)
            self.assertTrue(
                result["references"],
                f"Trigger word '{word}' returned no references",
            )

    def test_fact_check_returns_references(self):
        result = method_index.plan_search("fact-check a viral video")
        self.assertTrue(result["references"])
        refs = " ".join(result["references"])
        self.assertIn("fact-checking.md", refs)

    def test_verify_claim_returns_references(self):
        result = method_index.plan_search("verify a claim")
        self.assertTrue(result["references"])

    def test_evaluate_evidence_returns_references(self):
        result = method_index.plan_search("evaluate evidence")
        self.assertTrue(result["references"])
        refs = " ".join(result["references"])
        self.assertIn("evaluate-evidence.md", refs)

    def test_trace_username_returns_references(self):
        result = method_index.plan_search("trace username alice123")
        self.assertTrue(result["references"])

    def test_trace_email_returns_references(self):
        result = method_index.plan_search("trace an email")
        self.assertTrue(result["references"])

    def test_domain_lookup_returns_references(self):
        result = method_index.plan_search("domain lookup example.com")
        self.assertTrue(result["references"])

    def test_osint_returns_references(self):
        result = method_index.plan_search("osint investigation")
        self.assertTrue(result["references"])

    def test_how_to_research_returns_references(self):
        result = method_index.plan_search("how to research")
        self.assertTrue(result["references"])

    def test_tradecraft_returns_references(self):
        result = method_index.plan_search("tradecraft")
        self.assertTrue(result["references"])

    def test_no_method_match_falls_back(self):
        result = method_index.plan_search("random unrelated topic")
        self.assertTrue(result["references"])

    def test_empty_query_raises(self):
        with self.assertRaises(ValueError):
            method_index.plan_search("")

    def test_command_injection_safety(self):
        result = method_index.plan_search('foo" && rm -rf /')
        self.assertTrue(result["commands"])
        dangerous = {"&&", "||", ";", "|"}
        for cmd in result["commands"]:
            parts = shlex.split(cmd)
            self.assertEqual(parts[0], "kbs")
            self.assertIn('foo" && rm -rf /', parts)
            self.assertFalse(
                any(p in dangerous for p in parts),
                f"Shell operator leaked in command: {cmd}",
            )


if __name__ == "__main__":
    unittest.main()
