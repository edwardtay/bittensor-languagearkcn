from languageark.metrics import bleu_score, chrf_plus_plus, chrf_score, wer


def test_chrf_perfect_match():
    assert chrf_score("hello world", "hello world") > 0.99
    assert chrf_plus_plus("你好世界", "你好世界") > 0.99


def test_chrf_zero_match():
    assert chrf_score("abc", "xyz") < 0.1


def test_chrf_partial_match_chinese():
    # Some character overlap
    assert 0.2 < chrf_plus_plus("你吃饱了吗", "你吃了吗") < 0.95


def test_bleu_perfect_and_zero():
    assert bleu_score("hello world", "hello world") >= 0.99
    assert bleu_score("", "anything") == 0.0


def test_wer_perfect_is_zero():
    assert wer("the cat sat", "the cat sat") == 0.0
    assert wer("你好世界", "你好世界") == 0.0


def test_wer_full_substitution_is_one():
    assert wer("xyz qrs", "the cat") == 1.0


def test_wer_cjk_per_character():
    # 4-char reference, 1 substituted → WER 0.25
    score = wer("你好再见", "你好世界")
    assert 0.4 < score < 0.6


def test_wer_empty_hypothesis():
    assert wer("", "the cat") == 1.0
    assert wer("", "") == 0.0
