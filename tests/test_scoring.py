import math

import pytest

from languageark.scoring import (
    MinerScore,
    ScoreWeights,
    composite_score,
    normalize_elo,
    normalize_weight_vector,
    sigmoid,
)


def test_weights_must_sum_to_one():
    with pytest.raises(ValueError):
        ScoreWeights(elo=0.5, bleu=0.5, flores=0.5)


def test_default_weights_sum_to_one():
    w = ScoreWeights()
    assert math.isclose(w.elo + w.bleu + w.flores, 1.0)


def test_sigmoid_midpoint():
    assert math.isclose(sigmoid(0.0), 0.5, abs_tol=1e-9)


def test_normalize_elo_baseline():
    assert math.isclose(normalize_elo(1500.0), 0.5, abs_tol=1e-9)


def test_normalize_elo_monotonic():
    assert normalize_elo(1700.0) > normalize_elo(1500.0) > normalize_elo(1300.0)


def test_composite_baseline():
    # A miner exactly at the median across all three signals scores 0.5.
    s = composite_score(elo_rating=1500.0, bleu_bt=0.5, flores=0.5)
    assert isinstance(s, MinerScore)
    assert math.isclose(s.composite, 0.5, abs_tol=1e-9)


def test_composite_weights_applied():
    # All-perfect except BLEU at 0.0 → composite = 0.4·1 + 0 + 0.3·1 = 0.7
    s = composite_score(elo_rating=3000.0, bleu_bt=0.0, flores=1.0)
    assert 0.69 < s.composite < 0.71  # elo_norm ≈ 1


def test_composite_rejects_out_of_range():
    with pytest.raises(ValueError):
        composite_score(elo_rating=1500.0, bleu_bt=1.5, flores=0.5)
    with pytest.raises(ValueError):
        composite_score(elo_rating=1500.0, bleu_bt=0.5, flores=-0.1)
    with pytest.raises(ValueError):
        composite_score(elo_rating=10000.0, bleu_bt=0.5, flores=0.5)


def test_normalize_weight_vector_sums_to_one():
    raw = {0: 0.7, 1: 0.2, 2: 0.1}
    w = normalize_weight_vector(raw)
    assert math.isclose(sum(w.values()), 1.0)
    assert w[0] > w[1] > w[2]


def test_normalize_weight_vector_clamps_negatives():
    raw = {0: 0.5, 1: -0.2, 2: 0.5}
    w = normalize_weight_vector(raw)
    assert w[1] == 0.0
    assert math.isclose(sum(w.values()), 1.0)


def test_normalize_weight_vector_all_zero_is_uniform():
    raw = {0: 0.0, 1: 0.0, 2: 0.0}
    w = normalize_weight_vector(raw)
    assert all(math.isclose(v, 1 / 3) for v in w.values())
