from languageark.eval_samples import (
    ALL_MINERS,
    EVAL_SAMPLES_NAN,
    MINER_0_OUTPUTS,
    MINER_1_OUTPUTS,
    MINER_2_OUTPUTS,
)


def test_eval_samples_have_required_fields():
    assert len(EVAL_SAMPLES_NAN) >= 5
    for s in EVAL_SAMPLES_NAN:
        assert s.hokkien
        assert s.poj
        assert s.mandarin_gold


def test_miner_0_is_perfect_match():
    """The 'professional' miner should match gold exactly."""
    for s in EVAL_SAMPLES_NAN:
        assert MINER_0_OUTPUTS[s.hokkien] == s.mandarin_gold


def test_miner_1_is_competent_but_different():
    """The 'competent' miner outputs differ from gold but cover all samples."""
    diffs = 0
    for s in EVAL_SAMPLES_NAN:
        if MINER_1_OUTPUTS[s.hokkien] != s.mandarin_gold:
            diffs += 1
    assert diffs >= 1, "competent miner should differ on at least one sample"


def test_miner_2_is_clearly_worse():
    """The 'poor' miner should differ from gold on all samples."""
    diffs = sum(1 for s in EVAL_SAMPLES_NAN if MINER_2_OUTPUTS[s.hokkien] != s.mandarin_gold)
    assert diffs >= 5, "poor miner should differ on most samples"


def test_all_miners_keyed_by_uid():
    assert set(ALL_MINERS.keys()) == {0, 1, 2}


def test_all_miners_cover_all_samples():
    for uid, outputs in ALL_MINERS.items():
        for s in EVAL_SAMPLES_NAN:
            assert s.hokkien in outputs, f"uid={uid} missing {s.hokkien}"
