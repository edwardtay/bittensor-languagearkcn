from languageark.eval_samples import (
    flores_chinese_family_eval_set,
    generate_miner_outputs,
    hokkien_eval_set,
)


def test_hokkien_set_has_required_fields():
    samples = hokkien_eval_set()
    assert len(samples) >= 5
    for s in samples:
        assert s.source_text
        assert s.gold_target
        assert s.source_lang == "nan"
        assert s.target_lang == "zh-Hans"


def test_flores_yue_real_data_loaded():
    """REAL FLORES-200 Cantonese-Mandarin pairs must load."""
    samples = flores_chinese_family_eval_set(n=10)
    assert len(samples) == 10
    for s in samples:
        assert s.source_lang == "yue_Hant"
        assert s.target_lang == "zho_Hans"
        # These are real translated sentences, should be substantive
        assert len(s.source_text) > 10
        assert len(s.gold_target) > 10


def test_miner_0_returns_gold_exactly():
    samples = hokkien_eval_set()
    outputs = generate_miner_outputs(samples)
    for s in samples:
        assert outputs[0][s.source_text] == s.gold_target


def test_miner_2_degrades_significantly():
    samples = hokkien_eval_set()
    outputs = generate_miner_outputs(samples)
    diffs = sum(1 for s in samples if outputs[2][s.source_text] != s.gold_target)
    assert diffs >= len(samples) - 1, "poor miner should differ from gold on nearly all samples"


def test_miner_outputs_deterministic():
    """Same input → same outputs, even after re-call. Important for replay."""
    samples = hokkien_eval_set()
    o1 = generate_miner_outputs(samples)
    o2 = generate_miner_outputs(samples)
    assert o1[1] == o2[1]
    assert o1[2] == o2[2]


def test_miner_outputs_cover_all_uids():
    samples = hokkien_eval_set()
    outputs = generate_miner_outputs(samples)
    assert set(outputs.keys()) == {0, 1, 2}
    for uid, out in outputs.items():
        for s in samples:
            assert s.source_text in out, f"uid={uid} missing source"
