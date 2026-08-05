"""Hard integrity gate for generated review text, independent of LaTeX and synthesis."""

import re


def _sentences(text) -> list[str]:
    """Dependency invariant: punctuation splitting keeps this gate stdlib-only."""
    if not isinstance(text, str):
        return []
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text.strip()) if part.strip()]


def _words(text) -> list[str]:
    """Comparison invariant: punctuation and case must not alter attribution."""
    return re.findall(r"[a-z0-9]+", text.lower())


def check_quotes(quotes) -> dict:
    """Fail closed when a quote does not match a sentence in its attributed source."""
    flags = []
    for quote in quotes:
        quote_text = quote.get("quote_text", "")
        quote_words = _words(quote_text)
        source_sentences = _sentences(quote.get("source_text", ""))
        matches_source = bool(quote_words) and any(
            quote_words == _words(source_sentence)
            for source_sentence in source_sentences
        )
        if not matches_source:
            flags.append(
                {
                    "quote_text": quote_text,
                    "source_id": quote.get("source_id", ""),
                    "signal": "attribution",
                }
            )
    return {"status": "flagged", "flags": flags} if flags else {"status": "pass"}
