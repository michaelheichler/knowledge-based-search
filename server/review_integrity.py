"""Hard integrity gate for generated review text, independent of LaTeX and synthesis."""

import re
from difflib import SequenceMatcher

WORD_RATIO_THRESHOLD = 0.7
LONGEST_BLOCK_WORDS = 8

# ponytail: starting thresholds need retuning against real generated reviews.


def _sentences(text) -> list[str]:
    """Dependency invariant: punctuation splitting keeps this gate stdlib-only."""
    if not isinstance(text, str):
        return []
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text.strip()) if part.strip()]


def _words(text) -> list[str]:
    """Comparison invariant: punctuation must not alter lexical similarity."""
    return re.findall(r"[a-z0-9]+", text.lower())


def _flag(claim_sentence, source_id, matched_source_sentence, signal, score) -> dict:
    """Report invariant: each signal carries its source and score."""
    return {
        "claim_sentence": claim_sentence,
        "source_id": source_id,
        "matched_source_sentence": matched_source_sentence,
        "signal": signal,
        "score": score,
    }


def _signal_flags(claim_sentence, source_id, source_sentence, ratio, longest_block) -> list[dict]:
    """Threshold invariant: each independent signal remains reportable."""
    flags = []
    if ratio >= WORD_RATIO_THRESHOLD:
        flags.append(
            _flag(claim_sentence, source_id, source_sentence, "word_ratio", ratio)
        )
    if longest_block >= LONGEST_BLOCK_WORDS:
        flags.append(
            _flag(
                claim_sentence,
                source_id,
                source_sentence,
                "longest_block",
                longest_block,
            )
        )
    return flags


def _pair_flags(claim_sentence, source_id, matched_source_sentence) -> list[dict]:
    """Pair invariant: lexical comparison uses one matcher for both signals."""
    claim_words = _words(claim_sentence)
    source_words = _words(matched_source_sentence)
    if not claim_words or not source_words:
        return []
    matcher = SequenceMatcher(None, claim_words, source_words, autojunk=False)
    ratio = matcher.ratio()
    longest_block = max(
        (block.size for block in matcher.get_matching_blocks()),
        default=0,
    )
    return _signal_flags(
        claim_sentence,
        source_id,
        matched_source_sentence,
        ratio,
        longest_block,
    )


def _lexical_flags(claim_sentence, source_id, source_text) -> list[dict]:
    """Lexical invariant: any cited-source sentence can block finalization."""
    if not _words(claim_sentence):
        return []
    flags = []
    source_sentences = _sentences(source_text)
    # Invariant: flags cover processed sentences. Variant: unprocessed sentences.
    for matched_source_sentence in source_sentences:
        flags.extend(_pair_flags(claim_sentence, source_id, matched_source_sentence))
    return flags


def check_claims(claims) -> dict:
    """Fail closed when any claim resembles text from its attributed source."""
    flags = []
    # Invariant: flags cover processed claims. Variant: unprocessed claims.
    for claim in claims:
        flags.extend(
            _lexical_flags(
                claim.get("claim_sentence", ""),
                claim.get("source_id", ""),
                claim.get("source_text", ""),
            )
        )
    return {"status": "flagged", "flags": flags} if flags else {"status": "pass"}
