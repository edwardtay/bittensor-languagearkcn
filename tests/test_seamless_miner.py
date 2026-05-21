"""Integration test for the real SeamlessM4T-v2 miner.

Skipped if `transformers` or `torch` aren't installed, or if the model
isn't cached locally — we don't want the test suite to download 9GB on CI.

To enable: install miner extras (`pip install -e ".[miner]"`) and either
cache the model first (`huggingface-cli download facebook/seamless-m4t-v2-large`)
or set env `LANGUAGEARK_RUN_SEAMLESS_TEST=1` to allow auto-download.
"""
from __future__ import annotations

import os

import pytest


def _seamless_available() -> bool:
    try:
        import torch  # noqa: F401
        import transformers  # noqa: F401
        return True
    except ImportError:
        return False


@pytest.mark.skipif(not _seamless_available(), reason="transformers/torch not installed")
def test_seamless_module_imports():
    """The miner module should import without loading the model."""
    from languageark import seamless_miner
    assert hasattr(seamless_miner, "translate")
    assert hasattr(seamless_miner, "translate_batch")
    assert seamless_miner.SEAMLESS_HOKKIEN == "nan"
    assert seamless_miner.SEAMLESS_MANDARIN == "cmn"


@pytest.mark.skipif(
    not _seamless_available() or not os.environ.get("LANGUAGEARK_RUN_SEAMLESS_TEST"),
    reason="Model download is 9GB; opt in with LANGUAGEARK_RUN_SEAMLESS_TEST=1",
)
def test_seamless_translates_hokkien_to_mandarin():
    """End-to-end: load model, translate one Hokkien sentence, get Mandarin out."""
    from languageark.seamless_miner import translate

    out = translate("你食飽未?", src_lang="nan", tgt_lang="cmn")
    assert isinstance(out, str)
    assert len(out) > 0
    # Real Mandarin output should contain at least one Han character
    assert any("一" <= c <= "鿿" for c in out), f"expected Han chars, got: {out!r}"
