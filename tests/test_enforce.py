"""Tests for book-backed query enforcement, retries, and quality labels."""

import importlib
import io
import json
import re

import pytest

cli = importlib.import_module("cli")
enforce = importlib.import_module("enforce")
trust = importlib.import_module("trust")
engines = importlib.import_module("engines")
rag = importlib.import_module("rag")
search_core = importlib.import_module("search_core")
search_deep = importlib.import_module("search_deep")

_BOOK_TAG = re.compile(
    r"(?:osint-techniques|osint-resources) ch\d+\b|exposingtheinvisible google-dorking"
)


def _assert_book_tags(corrections) -> None:
    assert corrections
    assert all(_BOOK_TAG.search(item["reason"]) for item in corrections)


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("Find John Smith", '"John Smith"'),
        ("Find John Smith LinkedIn", '"John Smith" LinkedIn'),
        ("Find Latest Climate Change Reports", "Latest Climate Change Reports"),
        ("why does CAN bus fail on startup", "CAN bus fail startup"),
        ("why is US policy changing today", "US policy changing today"),
        ("why is IT failing today", "IT failing today"),
        ("john.smith@example.com", '"john.smith@example.com"'),
        (
            "climate records filetype:xls",
            "climate records (filetype:xls OR filetype:xlsx OR filetype:csv)",
        ),
        (
            "exclude -filetype:doc",
            "exclude -filetype:doc -filetype:docx",
        ),
        (
            "Could you please find latest climate change reports for me",
            "latest climate change reports",
        ),
        (
            'Please find "climate change" site:who.int -blog OR site:un.org',
            '"climate change" site:who.int -blog OR site:un.org',
        ),
    ],
)
def test_enforce_query_table(query, expected) -> None:
    """Rewrite representative agent queries without losing protected syntax."""
    rewritten, corrections = enforce.enforce_query(query)

    assert rewritten == expected
    _assert_book_tags(corrections)


def test_enforce_query_uses_exact_context_and_is_idempotent() -> None:
    """Honor structured exact segments and avoid re-expanding an OR family."""
    first, corrections = enforce.enforce_query(
        "research Alpha Beta filetype:doc", {"exact_segments": ["alpha beta"]}
    )
    second, repeated = enforce.enforce_query(first, {"exact_segments": ["alpha beta"]})

    assert first == 'research "Alpha Beta" (filetype:doc OR filetype:docx)'
    assert second == first
    assert {item["kind"] for item in corrections} == {"quote-exact", "expand-filetype"}
    _assert_book_tags(corrections)
    assert repeated == []
    nested = enforce.enforce_query(
        'research "prefix Alpha Beta suffix"',
        {"exact_segments": ["alpha beta"]},
    )
    assert nested == ('research "prefix Alpha Beta suffix"', [])
    substring = enforce.enforce_query(
        "malpha betamax", {"exact_segments": ["alpha beta"]}
    )
    assert substring == ("malpha betamax", [])


@pytest.mark.parametrize(
    "query",
    [
        "Warum Funktioniert Der Neue Motor Heute Nicht",
        "Warum Funktioniert Motor",
        "TypeError: Cannot Read Property of Undefined",
        "HTTPError: 404 Not Found",
        "Cannot Read Property of Undefined",
        "Alice Bob Carol Dave",
    ],
)
def test_title_case_guard_preserves_ambiguous_text(query) -> None:
    """Capitalizing languages and error text are not reliable entity signals."""
    assert enforce.enforce_query(query) == (query, [])


def test_filetype_pdf_passes_through_without_false_correction() -> None:
    """Keep unrelated spacing and the one-member PDF family literal."""
    assert enforce.enforce_query("alpha  beta") == ("alpha  beta", [])
    assert enforce.enforce_query("audit  filetype:pdf") == (
        "audit  filetype:pdf",
        [],
    )


def test_filetype_text_inside_url_is_not_an_operator() -> None:
    """Preserve URL query values that happen to contain filetype text."""
    query = "https://example.com/?q=filetype:xls"
    assert enforce.enforce_query(query) == (query, [])


def test_filetype_expansion_is_idempotent_for_both_polarities() -> None:
    """Re-enforcing an already expanded query must not stack duplicates."""
    for query in ("report filetype:doc", "report -filetype:doc"):
        expanded, first = enforce.enforce_query(query)
        again, trail = enforce.enforce_query(expanded)
        assert first
        assert again == expanded
        assert trail == []


def _hit(
    url="https://example.com/result", title="John Smith profile", snippet="profile"
):
    return {
        "title": title,
        "url": url,
        "snippet": snippet,
        "engine": "duckduckgo",
        "engines": ["duckduckgo"],
        "date": "",
        "relevance": 0.5,
    }


def _install_rank_stub(monkeypatch):
    monkeypatch.setattr(rag, "rank", lambda query, docs: list(docs))


def test_search_core_wires_exact_segment_context(monkeypatch) -> None:
    """Structured exact hints must reach the shared dispatch boundary."""
    calls = []

    def fake_search(query, config, **options) -> list:
        calls.append(query)
        return [_hit(), _hit("https://second.example/result")]

    _install_rank_stub(monkeypatch)
    monkeypatch.setattr(engines, "search", fake_search)

    response = search_core.quick_web_search(
        "research Alpha Beta", {}, context={"exact_segments": ["alpha beta"]}
    )

    assert calls == ['research "Alpha Beta"']
    assert response["query"] == 'research "Alpha Beta"'


def test_zero_results_recover_by_relaxing_quotes(monkeypatch) -> None:
    """Retry an exact phrase in-process and expose the attempt."""
    calls = []

    def fake_search(query, config, **options) -> list:
        """Return a hit only after quote relaxation."""
        calls.append(query)
        if query == "John Smith":
            return [_hit("https://one.example/a"), _hit("https://two.example/b")]
        return []

    _install_rank_stub(monkeypatch)
    monkeypatch.setattr(engines, "search", fake_search)

    response = search_core.quick_web_search("Find John Smith", {})

    assert calls == ['"John Smith"', "John Smith"]
    assert response["results"]
    assert [item["kind"] for item in response["corrections"]] == [
        "quote-proper-noun",
        "compress-agent-query",
        "relax-quotes",
    ]
    _assert_book_tags(response["corrections"])


def test_refinement_budget_caps_at_two_corrective_calls(monkeypatch) -> None:
    """Stop after quote relaxation and one operator reorder."""
    calls = []

    def empty_search(query, config, **options) -> list:
        """Record every attempted query while returning no hits."""
        calls.append(query)
        return []

    _install_rank_stub(monkeypatch)
    monkeypatch.setattr(engines, "search", empty_search)

    response = search_core.quick_web_search(
        '"John Smith" site:example.com filetype:pdf', {}
    )

    retry_kinds = [item["kind"] for item in response["corrections"]]
    assert len(calls) == 3
    assert retry_kinds == ["relax-quotes", "reorder-operators"]
    _assert_book_tags(response["corrections"])


def test_deep_fallback_does_not_reopen_exhausted_budget(monkeypatch) -> None:
    """Keep deep snippet fallback inside the same two-retry ceiling."""
    calls = []

    def empty_search(query, config, **options) -> list:
        """Record every primary dispatch while returning no hits."""
        calls.append(query)
        return []

    _install_rank_stub(monkeypatch)
    monkeypatch.setattr(engines, "search", empty_search)

    response = search_deep._deep_search(
        '"John Smith" site:example.com filetype:pdf', {}
    )

    assert len(calls) == 3
    assert search_deep._corrective_rounds(response) == 2
    _assert_book_tags(response["corrections"])


def test_weak_phrase_uses_wildcard_retry(monkeypatch) -> None:
    """Broaden a brittle exact phrase when only one hit supports it."""
    calls = []

    def weak_search(query, config, **options) -> list:
        """Return broader evidence only for the wildcard form."""
        calls.append(query)
        if "*" in query:
            return [_hit("https://one.example/a"), _hit("https://two.example/b")]
        return [_hit()]

    _install_rank_stub(monkeypatch)
    monkeypatch.setattr(engines, "search", weak_search)

    response = search_core.quick_web_search('"John Smith"', {})

    assert calls == ['"John Smith"', '"John * Smith"']
    assert response["quality"]["verification"] == "corroborated"
    assert response["corrections"][0]["kind"] == "wildcard-phrase"
    _assert_book_tags(response["corrections"])


def test_failed_wildcard_retry_keeps_effective_query(monkeypatch) -> None:
    """Report the query that produced retained hits after a failed retry."""
    calls = []

    def weak_search(query, config, **options) -> list:
        """Return one exact hit and no wildcard hits."""
        calls.append(query)
        return [] if "*" in query else [_hit()]

    _install_rank_stub(monkeypatch)
    monkeypatch.setattr(engines, "search", weak_search)

    response = search_core.quick_web_search('"John Smith"', {})

    assert calls == ['"John Smith"', '"John * Smith"']
    assert response["query"] == '"John Smith"'
    assert response["results"]


def test_noisy_results_use_progressive_negation(monkeypatch) -> None:
    """Spend the retry budget excluding frequent irrelevant snippet terms."""
    calls = []
    noise = [
        _hit(
            f"https://noise{index}.example/result", snippet="shopping coupon directory"
        )
        for index in range(5)
    ]

    def noisy_search(query, config, **options) -> list:
        """Return the same oversized irrelevant set for each bounded retry."""
        calls.append(query)
        return noise

    _install_rank_stub(monkeypatch)
    monkeypatch.setattr(engines, "search", noisy_search)

    response = search_core.quick_web_search("alpha", {})

    assert calls == ["alpha", "alpha -shopping", "alpha -shopping -coupon"]
    kinds = [item["kind"] for item in response["corrections"]]
    assert kinds == ["progressive-negation"] * 2
    _assert_book_tags(response["corrections"])


def test_environment_bypass_preserves_literal_query(monkeypatch) -> None:
    """Bypass both rewriting and corrective retries through the environment."""
    calls = []

    def fake_search(query, config, **options) -> list:
        """Capture the one literal engine dispatch."""
        calls.append(query)
        return []

    _install_rank_stub(monkeypatch)
    monkeypatch.setattr(engines, "search", fake_search)
    monkeypatch.setenv("KBS_NO_ENFORCE", "1")

    response = search_core.quick_web_search("  Could you find John Smith  ", {})

    assert calls == ["  Could you find John Smith  "]
    assert response["query"] == "  Could you find John Smith  "
    assert response["corrections"] == []


@pytest.mark.parametrize("use_flag", [False, True])
def test_deep_raw_dispatches_literal_query_once(monkeypatch, use_flag) -> None:
    """Both literal controls must share the same deep fallback decision."""
    calls = []

    def empty_search(query, config, **options) -> list:
        calls.append(query)
        return []

    _install_rank_stub(monkeypatch)
    monkeypatch.setattr(engines, "search", empty_search)
    if not use_flag:
        monkeypatch.setenv("KBS_NO_ENFORCE", "1")

    response = search_deep._deep_search(" literal ", {}, raw=use_flag)

    assert calls == [" literal "]
    assert response["query"] == " literal "
    assert response["corrections"] == []


def test_quality_gate_tags_tiers_and_diversity() -> None:
    """Expose cheap source tiers and distinct-domain corroboration."""
    tagged, quality = trust.quality_gate(
        [
            _hit("https://data.gov/report"),
            _hit("https://reuters.com/story"),
            _hit("https://zoominfo.com/company"),
            _hit("http://["),
        ]
    )

    assert [item["confidence"] for item in tagged] == [
        "primary",
        "primary",
        "weak",
        "unknown",
    ]
    assert quality["distinct_root_domains"] == 3
    assert quality["low_diversity"] is False
    assert quality["verification"] == "corroborated"


def test_untrusted_docs_subdomain_stays_unknown() -> None:
    """Do not grant trust from a docs or developer hostname prefix alone."""
    assert trust.source_tier("https://docs.attacker.example/page") == "unknown"
    assert trust.source_tier("https://data.gov.au/report") == "primary"


def test_unrelated_domains_do_not_claim_corroboration() -> None:
    """Require lexical support as well as independent domains."""
    _, quality = trust.quality_gate(
        [
            _hit("https://one.example/a", title="Alpha climate", snippet="warming"),
            _hit("https://two.example/b", title="Beta finance", snippet="markets"),
        ]
    )

    assert quality["distinct_root_domains"] == 2
    assert quality["supporting_root_domains"] == 1
    assert quality["verification"] == "single-source"


def test_generic_report_terms_do_not_claim_corroboration() -> None:
    """Publication labels cannot establish shared claim support."""
    _, quality = trust.quality_gate(
        [
            _hit(
                "https://one.example/a",
                title="Annual Report Alpha",
                snippet="climate warming",
            ),
            _hit(
                "https://two.example/b",
                title="Annual Report Beta",
                snippet="finance markets",
            ),
        ]
    )

    assert quality["verification"] == "single-source"
    assert quality["supporting_root_domains"] == 1


def test_root_domain_handles_country_and_tenant_suffixes() -> None:
    """Keep independent country and hosted-project domains distinct."""
    urls = ["https://a.co.nz", "https://b.co.nz", "https://foo.github.io"]
    assert [trust.root_domain(url) for url in urls] == [
        "a.co.nz",
        "b.co.nz",
        "foo.github.io",
    ]


def test_quality_gate_flags_collapsed_domains() -> None:
    """Flag a top set whose URLs collapse to two root domains."""
    _, quality = trust.quality_gate(
        [
            _hit("https://a.example.com/one"),
            _hit("https://b.example.com/two"),
            _hit("https://other.test/three"),
        ]
    )

    assert quality["distinct_root_domains"] == 2
    assert quality["low_diversity"] is True


def test_corrections_are_present_in_cli_json(monkeypatch) -> None:
    """Keep the correction trail intact in machine-readable CLI output."""
    trail = [
        {
            "kind": "compress-agent-query",
            "before": "please find alpha",
            "after": "alpha",
            "reason": "compressed to keyword form (osint-techniques ch24)",
        }
    ]

    def fake_quick(query, config, num_results=8, **options) -> dict:
        """Return a stable correction trail for CLI serialization."""
        return {"query": "alpha", "results": [], "corrections": trail}

    monkeypatch.setattr(search_core, "quick_web_search", fake_quick)
    stdout = io.StringIO()
    code = cli.main(["quick", "please", "find", "alpha", "--json"], stdout=stdout)

    assert code == cli.SUCCESS
    assert json.loads(stdout.getvalue())["corrections"] == trail


def test_human_output_renders_corrections_and_confidence() -> None:
    """Expose both correction provenance and source tiers to human callers."""
    data = {
        "summary": "answer",
        "citations": [
            {"title": tier, "url": f"https://{tier}.example", "confidence": tier}
            for tier in ("primary", "standard", "weak", "unknown")
        ],
        "corrections": [
            {
                "before": "please find alpha",
                "after": "alpha",
                "reason": "compressed to keyword form (osint-techniques ch24)",
            }
        ],
    }

    rendered = cli._render(data)

    for tier in ("primary", "standard", "weak", "unknown"):
        assert f"[confidence: {tier}]" in rendered
    assert "corrections: please find alpha -> alpha" in rendered


def test_cli_raw_flag_reaches_search_core(monkeypatch) -> None:
    """Forward explicit literal mode without changing the query text."""
    captured = []

    def fake_quick(query, config, num_results=8, **options) -> dict:
        """Capture literal-mode keyword arguments."""
        captured.append((query, options))
        return {"query": query, "results": [], "corrections": []}

    monkeypatch.setattr(search_core, "quick_web_search", fake_quick)

    assert cli.main(["quick", "Please", "Find", "Alpha", "--raw"]) == cli.SUCCESS
    assert captured == [("Please Find Alpha", {"raw": True})]


def test_cli_raw_stdin_preserves_surrounding_whitespace(monkeypatch) -> None:
    """Pass raw standard input to search_core without trimming it."""
    captured = []

    def fake_quick(query, config, num_results=8, **options) -> dict:
        """Capture the literal standard-input query."""
        captured.append(query)
        return {"query": query, "results": [], "corrections": []}

    monkeypatch.setattr(search_core, "quick_web_search", fake_quick)
    stdin = io.StringIO("  literal query  \n")
    stdout = io.StringIO()

    code = cli.main(["quick", "-", "--raw"], stdin=stdin, stdout=stdout)

    assert code == cli.SUCCESS
    assert captured == ["  literal query  \n"]

    captured.clear()
    monkeypatch.setenv("KBS_NO_ENFORCE", "1")
    stdin = io.StringIO("  environment literal  \n")
    code = cli.main(["quick", "-"], stdin=stdin, stdout=stdout)

    assert code == cli.SUCCESS
    assert captured == ["  environment literal  \n"]
