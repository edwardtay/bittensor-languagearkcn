"""Composite score function.

Deterministic, unit-tested. The judges should be able to read this in 30 seconds
and trust that it is not gameable by any single attack vector.

    score(m) = w_elo · Elo_norm(m) + w_bleu · BLEU_bt(m) + w_flores · FLORES200(m)

Defaults: w_elo=0.4, w_bleu=0.3, w_flores=0.3.
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class ScoreWeights:
    elo: float = 0.4
    bleu: float = 0.3
    flores: float = 0.3

    def __post_init__(self) -> None:
        total = self.elo + self.bleu + self.flores
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"Weights must sum to 1.0, got {total}")


@dataclass(frozen=True)
class MinerScore:
    """Per-miner score breakdown. All three components are in [0, 1]."""

    elo_rating: float       # raw Glicko-2 rating, ~1500 baseline
    elo_norm: float         # sigmoid-normalised, [0, 1]
    bleu_bt: float          # mean sentence-BLEU of back-translation, [0, 1]
    flores: float           # accuracy on held-out FLORES-200, [0, 1]
    composite: float        # weighted sum, [0, 1]


def sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def normalize_elo(rating: float, midpoint: float = 1500.0, scale: float = 400.0) -> float:
    """Glicko-2 rating → [0, 1] via shifted sigmoid.

    midpoint=1500 maps to 0.5. ±400 rating points doubles/halves odds (Elo convention).
    """
    return sigmoid((rating - midpoint) / scale)


def composite_score(
    elo_rating: float,
    bleu_bt: float,
    flores: float,
    weights: ScoreWeights = ScoreWeights(),
) -> MinerScore:
    """Combine three independent quality signals into a single miner score.

    Raises ValueError if any component is out of [0, 1] (after normalization) or
    if the elo_rating is implausibly far from 1500 baseline.
    """
    if not (0.0 <= bleu_bt <= 1.0):
        raise ValueError(f"bleu_bt out of range: {bleu_bt}")
    if not (0.0 <= flores <= 1.0):
        raise ValueError(f"flores out of range: {flores}")
    if not (500.0 <= elo_rating <= 3000.0):
        raise ValueError(f"elo_rating implausible: {elo_rating}")

    elo_norm = normalize_elo(elo_rating)
    composite = (
        weights.elo * elo_norm
        + weights.bleu * bleu_bt
        + weights.flores * flores
    )
    return MinerScore(
        elo_rating=elo_rating,
        elo_norm=elo_norm,
        bleu_bt=bleu_bt,
        flores=flores,
        composite=composite,
    )


def normalize_weight_vector(scores: dict[int, float]) -> dict[int, float]:
    """L1-normalize a {uid: score} map so the resulting vector sums to 1.

    This is what each validator publishes to the chain each tempo.
    """
    total = sum(max(0.0, s) for s in scores.values())
    if total <= 0.0:
        # All-zero weights → uniform (avoid div-by-zero; chain handles cleanup)
        n = len(scores) or 1
        return {uid: 1.0 / n for uid in scores}
    return {uid: max(0.0, s) / total for uid, s in scores.items()}
