"""Verify that our Synapse types are REAL bt.Synapse subclasses."""
import pytest


def test_bittensor_sdk_available():
    """If this fails, the rest of the chain integration is fiction."""
    import bittensor as bt
    assert bt.__version__


def test_hokkien_mt_is_real_bt_synapse():
    import bittensor as bt
    from languageark.bt_protocol import BT_AVAILABLE, HokkienMT
    assert BT_AVAILABLE
    s = HokkienMT(text="你食飽未?", src_lang="nan", tgt_lang="zh-Hans")
    assert isinstance(s, bt.Synapse)
    assert s.name == "HokkienMT"


def test_hokkien_asr_is_real_bt_synapse():
    import bittensor as bt
    from languageark.bt_protocol import HokkienASR
    s = HokkienASR(audio_b64="abc", target_script="poj")
    assert isinstance(s, bt.Synapse)
    assert s.target_script == "poj"


def test_synapse_round_trip_fields():
    from languageark.bt_protocol import HokkienMT
    s = HokkienMT(text="hi", src_lang="nan", tgt_lang="en")
    s.translation = "the response"
    assert s.translation == "the response"


def test_flores_data_present():
    """data/flores/ must contain real corpora — proof we did the data work."""
    from languageark.flores_loader import is_available, load_flores_pairs
    assert is_available(), "Missing FLORES data. Run: ./scripts/fetch_flores.sh"
    pairs = load_flores_pairs("yue_Hant", "zho_Hans", "dev")
    assert len(pairs) >= 990, f"Expected ~997 sentences, got {len(pairs)}"
    # spot check that we got real-looking parallel text
    assert "週" in pairs[0].src_text or "周" in pairs[0].src_text
    assert "斯坦福" in pairs[0].tgt_text or "史丹福" in pairs[0].src_text
