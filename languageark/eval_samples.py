"""Eval data + per-miner synthetic outputs.

Honesty notes:

1. **Hokkien-Mandarin pairs are curated by hand** — from Taiwan MoE Hokkien
   dictionary entries and common diaspora usage. FLORES-200 has no Hokkien.
   This 10-pair set is a starting point; the subnet's product IS scaling
   this corpus via the speaker DAO.

2. **Cantonese-Mandarin pairs are REAL FLORES-200** — 997 sentences with
   professional translators. Loaded from `data/flores/yue_Hant.dev` etc.

3. **Per-miner outputs are generated, not handwritten** — `generate_miner_outputs`
   degrades the gold reference by deterministic noise (char dropout / shuffling)
   to produce three quality tiers. This is honest about being synthetic.
"""
from __future__ import annotations

import random
from dataclasses import dataclass

from .flores_loader import HOKKIEN_PAIRS, FloresPair, HokkienPair, is_available, load_flores_pairs


@dataclass(frozen=True)
class EvalSample:
    """Unified eval-pair shape for both Hokkien (curated) + Cantonese (FLORES)."""

    source_text: str
    source_lang: str       # "nan" | "yue_Hant"
    gold_target: str       # always zh-Hans Mandarin
    target_lang: str       # "zh-Hans"


def hokkien_eval_set() -> list[EvalSample]:
    """The 10 curated Hokkien-Mandarin pairs (no FLORES coverage)."""
    return [
        EvalSample(source_text=p.hokkien_han, source_lang="nan",
                   gold_target=p.mandarin, target_lang="zh-Hans")
        for p in HOKKIEN_PAIRS
    ]


def flores_chinese_family_eval_set(n: int = 20) -> list[EvalSample]:
    """First `n` REAL FLORES-200 Cantonese↔Mandarin pairs.

    Used as a "Chinese-language-family" proxy — FLORES has no Hokkien but does
    have professional Cantonese-Mandarin pairs. We don't claim this measures
    Hokkien quality; it measures Chinese-family translation competence,
    which is correlated.
    """
    if not is_available():
        return []
    pairs = load_flores_pairs(src_lang="yue_Hant", tgt_lang="zho_Hans", split="dev")[:n]
    return [
        EvalSample(source_text=p.src_text, source_lang="yue_Hant",
                   gold_target=p.tgt_text, target_lang="zho_Hans")
        for p in pairs
    ]


# ─── Synthetic miner outputs (deterministic noise schedule) ────────

def _degrade(text: str, fraction: float, seed: int) -> str:
    """Drop `fraction` of characters at random (deterministic via seed).

    fraction=0.0 → return text unchanged
    fraction=0.3 → ~30% of characters dropped
    fraction=0.6 → severely degraded
    """
    if fraction <= 0:
        return text
    rng = random.Random(seed)
    return "".join(c for c in text if rng.random() > fraction)


def generate_miner_outputs(samples: list[EvalSample]) -> dict[int, dict[str, str]]:
    """Three quality tiers, generated deterministically from real eval samples.

      uid=0 (professional): exact gold match
      uid=1 (competent):    light degradation (~15% char drop)
      uid=2 (poor):         heavy degradation (~50% char drop)

    Returns: {uid: {source_text: predicted_mandarin}}.
    """
    outputs: dict[int, dict[str, str]] = {0: {}, 1: {}, 2: {}}
    for i, s in enumerate(samples):
        outputs[0][s.source_text] = s.gold_target
        outputs[1][s.source_text] = _degrade(s.gold_target, fraction=0.15, seed=i)
        outputs[2][s.source_text] = _degrade(s.gold_target, fraction=0.50, seed=i)
    return outputs
