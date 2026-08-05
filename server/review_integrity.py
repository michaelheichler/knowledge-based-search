"""Hard integrity gate for generated review text, independent of LaTeX and synthesis."""

import contextlib
import re
from difflib import SequenceMatcher

import rag

WORD_RATIO_THRESHOLD = 0.7
LONGEST_BLOCK_WORDS = 8
EMBEDDING_COSINE_THRESHOLD = 0.90

# ponytail: starting thresholds need retuning against real generated reviews.


def _sentences(text) -> list[str]:
    """Dependency invariant: punctuation splitting keeps this gate stdlib-only."""
    if not isinstance(text, str):
        return []
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text.strip()) if part.strip()]


def _words(text) -> list[str]:
    """Comparison invariant: punctuation must not alter lexical similarity."""
    return re.findall(r"[a-z0-9]+", text.lower())


def _flag(pair, signal, score) -> dict:
    """Report invariant: each signal carries its source and score."""
    claim_sentence, source_id, source_sentence = pair
    return {
        "claim_sentence": claim_sentence,
        "source_id": source_id,
        "matched_source_sentence": source_sentence,
        "signal": signal,
        "score": score,
    }


def _signal_flags(pair, ratio, longest_block) -> list[dict]:
    """Threshold invariant: each independent signal remains reportable."""
    flags = []
    if ratio >= WORD_RATIO_THRESHOLD:
        flags.append(_flag(pair, "word_ratio", ratio))
    if longest_block >= LONGEST_BLOCK_WORDS:
        flags.append(_flag(pair, "longest_block", longest_block))
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
        (claim_sentence, source_id, matched_source_sentence), ratio, longest_block
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


def _claim_pairs(claim) -> list[tuple[str, str, str]]:
    """Attribution invariant: a claim pairs only with its own source sentences."""
    claim_sentence = claim.get("claim_sentence", "")
    if not _words(claim_sentence):
        return []
    source_id = claim.get("source_id", "")
    return [
        (claim_sentence, source_id, source_sentence)
        for source_sentence in _sentences(claim.get("source_text", ""))
        if _words(source_sentence)
    ]


def _comparison_pairs(claims) -> list[tuple[str, str, str]]:
    """Attribution invariant: pairs never cross a claim's cited source boundary."""
    pairs = []
    for claim in claims:
        pairs.extend(_claim_pairs(claim))
    return pairs


def _embedding_vectors(pairs) -> dict[str, object] | None:
    """Optional-layer invariant: unavailable embeddings disable only semantic checks."""
    if not pairs:
        return {}
    texts = []
    for claim_sentence, _, source_sentence in pairs:
        texts.extend((claim_sentence, source_sentence))
    unique_texts = list(dict.fromkeys(texts))
    vectors = None
    with contextlib.suppress(Exception):
        vectors = rag.embed(unique_texts)
    if vectors is None or len(vectors) != len(unique_texts):
        return None
    return dict(zip(unique_texts, vectors))


def _embedding_pair_flag(pair, vectors) -> dict | None:
    """Cosine invariant: only an attributed pair can produce a semantic flag."""
    with contextlib.suppress(Exception):
        claim_sentence, _, source_sentence = pair
        score = rag._cosine(vectors[claim_sentence], vectors[source_sentence])
        if score >= EMBEDDING_COSINE_THRESHOLD:
            return _flag(pair, "embedding_cosine", score)
    return None


def _embedding_flags(pairs, vectors) -> list[dict]:
    """Semantic invariant: every pair receives one optional cosine comparison."""
    flags = []
    # Invariant: flags cover processed pairs. Variant: unprocessed pairs.
    for pair in pairs:
        flag = _embedding_pair_flag(pair, vectors)
        if flag is not None:
            flags.append(flag)
    return flags


def check_claims(claims) -> dict:
    """Fail closed when any claim resembles text from its attributed source."""
    claims = list(claims)
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
    pairs = _comparison_pairs(claims)
    vectors = _embedding_vectors(pairs)
    if vectors is not None:
        flags.extend(_embedding_flags(pairs, vectors))
    return {"status": "flagged", "flags": flags} if flags else {"status": "pass"}
