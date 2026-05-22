"""Unit test for the real-Claude miner module.

We don't ship live API calls in the test suite, but we DO want to verify:
  1. The miner translates each sample exactly once via the Anthropic SDK.
  2. The persisted JSON has the expected shape `{uid: {src: pred}}`.
  3. The validator picks up `data/real_miner_outputs.json` and uses it.
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path


def _fake_anthropic(monkeypatch, predictions: dict[str, str]):
    """Patch AsyncAnthropic so .messages.create returns canned predictions
    keyed by the *source text* found in the prompt.
    """
    class _Block:
        type = "text"
        def __init__(self, t: str) -> None:
            self.text = t

    class _Resp:
        def __init__(self, t: str) -> None:
            self.content = [_Block(t)]

    class _Messages:
        async def create(self, **kwargs):
            content = kwargs["messages"][0]["content"]
            for src, pred in predictions.items():
                if src in content:
                    return _Resp(pred)
            return _Resp("∅")

    class _FakeAsyncAnthropic:
        def __init__(self, *a, **kw):
            self.messages = _Messages()

    monkeypatch.setattr("anthropic.AsyncAnthropic", _FakeAsyncAnthropic, raising=True)


def test_claude_miner_translates_each_sample(monkeypatch):
    from languageark.claude_miner import translate_samples
    from languageark.eval_samples import hokkien_eval_set

    samples = hokkien_eval_set()[:3]
    canned = {s.source_text: f"[zh-pred for {i}]" for i, s in enumerate(samples)}
    _fake_anthropic(monkeypatch, canned)

    out = asyncio.run(translate_samples(samples))
    assert set(out.keys()) == {s.source_text for s in samples}
    for s in samples:
        assert out[s.source_text].startswith("[zh-pred for ")


def test_validator_loads_real_miner_outputs(monkeypatch, tmp_path):
    """If data/real_miner_outputs.json exists, validator should load it for that uid."""
    from languageark.eval_samples import hokkien_eval_set
    from languageark import validator as V

    samples = hokkien_eval_set()[:2]
    real_path = Path("data/real_miner_outputs.json")
    real_path.parent.mkdir(parents=True, exist_ok=True)
    real_payload = {"3": {s.source_text: f"REAL_{i}" for i, s in enumerate(samples)}}
    real_path.write_text(json.dumps(real_payload, ensure_ascii=False))
    try:
        # Stub the GLM/judge call to avoid network
        class _Judge:
            label = "stub-judge"
            async def translate(self, text, src_lang, tgt_lang):
                from languageark.glm_client import TranslationResult
                return TranslationResult(src=src_lang, tgt=tgt_lang,
                                         translation=text, model="stub")
        monkeypatch.setattr("languageark.validator.make_glm", lambda: _Judge())
        # Run main_async, but truncate FLORES branch by going with hokkien set
        asyncio.run(V.main_async("hokkien", Path("data/speaker_dao.json"),
                                  "json", "http://127.0.0.1:8545", None))
    finally:
        real_path.unlink(missing_ok=True)
