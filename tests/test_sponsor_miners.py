"""Import + interface smoke tests for the sponsor-stack miner wrappers.

The actual model weights are gigabytes — we don't load them in CI. We only
verify that the modules import cleanly, expose the documented entry points,
and raise the right error when their optional deps are missing.
"""
from __future__ import annotations

import pytest


def test_cosyvoice_miner_imports():
    from languageark import cosyvoice_miner as m
    assert m.DEFAULT_MODEL.startswith("FunAudioLLM/CosyVoice")
    assert callable(m.synthesize)


def test_sensevoice_miner_imports():
    from languageark import sensevoice_miner as m
    assert m.DEFAULT_MODEL.startswith("FunAudioLLM/SenseVoice")
    # The four target languages of the subnet are all in SenseVoice's set
    for code in ("zh", "yue", "nan", "hak"):
        assert code in m.SENSEVOICE_LANGS


def test_qwen_audio_miner_imports():
    from languageark import qwen_audio_miner as m
    assert m.DEFAULT_MODEL.startswith("Qwen/Qwen2-Audio")
    assert callable(m.understand)


def test_glm_voice_miner_imports():
    from languageark import glm_voice_miner as m
    assert m.DEFAULT_MODEL.startswith("THUDM/glm-4-voice")
    assert callable(m.speak)


def test_sensevoice_missing_dep_raises(monkeypatch):
    """When funasr is missing, transcribe() raises a friendly error."""
    from languageark import sensevoice_miner as m
    m._load_sensevoice.cache_clear()
    import builtins
    real_import = builtins.__import__

    def _no_funasr(name, *args, **kwargs):
        if name == "funasr":
            raise ImportError("funasr is not installed in this test env")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _no_funasr)
    with pytest.raises(RuntimeError, match="FunASR is not installed"):
        m._load_sensevoice()
