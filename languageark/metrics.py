"""Translation-quality metrics.

We expose four:
  - chrF       (character n-gram F-score)             — robust to tokenization
  - chrF++     (chrF with word-level extension)       — modern MT eval standard
  - sentence_bleu (sacrebleu)                          — legacy comparability
  - WER        (Word Error Rate, for ASR transcripts) — speech baseline

chrF / chrF++ are what WMT and FLORES papers actually score on. Sentence-BLEU
is noisy on short Chinese sentences; chrF handles that.
"""
from __future__ import annotations

from sacrebleu import CHRF, sentence_bleu, sentence_chrf


def chrf_score(hypothesis: str, reference: str, word_order: int = 0) -> float:
    """chrF (word_order=0) or chrF++ (word_order=2). Returns [0, 1]."""
    if not hypothesis or not reference:
        return 0.0
    metric = CHRF(word_order=word_order)
    return metric.sentence_score(hypothesis, [reference]).score / 100.0


def chrf_plus_plus(hypothesis: str, reference: str) -> float:
    """Standard chrF++."""
    return chrf_score(hypothesis, reference, word_order=2)


def bleu_score(hypothesis: str, reference: str) -> float:
    """Sentence-level BLEU. Returns [0, 1]."""
    if not hypothesis or not reference:
        return 0.0
    return min(1.0, sentence_bleu(hypothesis, [reference]).score / 100.0)


def wer(hypothesis: str, reference: str) -> float:
    """Word Error Rate for ASR. Returns [0, 1] where 0 is perfect.

    Edit distance / |reference| over whitespace tokens (or per-character for CJK).
    """
    if not reference:
        return 1.0 if hypothesis else 0.0

    # For CJK we compute per-character WER (no spaces in Chinese)
    is_cjk = any("一" <= c <= "鿿" for c in reference)
    ref_tokens = list(reference) if is_cjk else reference.split()
    hyp_tokens = list(hypothesis) if is_cjk else hypothesis.split()

    return min(1.0, _edit_distance(hyp_tokens, ref_tokens) / max(1, len(ref_tokens)))


def _edit_distance(a: list[str], b: list[str]) -> int:
    """Levenshtein distance, classical DP."""
    n, m = len(a), len(b)
    if n == 0:
        return m
    if m == 0:
        return n
    prev = list(range(m + 1))
    for i in range(1, n + 1):
        curr = [i] + [0] * m
        for j in range(1, m + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            curr[j] = min(
                curr[j - 1] + 1,        # insert
                prev[j] + 1,            # delete
                prev[j - 1] + cost,     # substitute
            )
        prev = curr
    return prev[m]
