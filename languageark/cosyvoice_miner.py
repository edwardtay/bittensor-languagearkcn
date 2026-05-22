"""Alibaba CosyVoice TTS miner — Hokkien text → speech audio.

CosyVoice (2024) is Alibaba's open-source SOTA Chinese-family TTS. Native
support for multilingual / multi-emotion / cross-speaker synthesis.
Released by Tongyi SpeechTeam. Weights on Hugging Face / ModelScope.

We wire it as the **default TTS miner backend** for the LanguageArk-CN
subnet. This is one of two reasons the sponsor narrative is real and not
just an integration claim:

  - Validator's LLM judge can be Qwen (Alibaba)         ← API tier
  - Miner's TTS model can be CosyVoice (Alibaba)        ← model tier
  - Miner's ASR model can be SenseVoice (Alibaba)       ← model tier

References:
  - HF: https://huggingface.co/FunAudioLLM/CosyVoice2-0.5B
  - Repo: https://github.com/FunAudioLLM/CosyVoice
"""
from __future__ import annotations

import functools
from pathlib import Path
from typing import Optional

import click

DEFAULT_MODEL = "FunAudioLLM/CosyVoice2-0.5B"


@functools.lru_cache(maxsize=1)
def _load_cosyvoice(model_id: str = DEFAULT_MODEL):
    """Lazy-load CosyVoice. Requires the `cosyvoice` extras."""
    try:
        # Library exposes a CosyVoice or CosyVoice2 class depending on version.
        try:
            from cosyvoice.cli.cosyvoice import CosyVoice2 as _Voice  # type: ignore
        except ImportError:
            from cosyvoice.cli.cosyvoice import CosyVoice as _Voice  # type: ignore
    except ImportError as e:
        raise RuntimeError(
            "CosyVoice is not installed. Install with: pip install cosyvoice "
            "(or follow https://github.com/FunAudioLLM/CosyVoice)"
        ) from e
    return _Voice(model_id)


def synthesize(text: str, *, lang: str = "zh", speaker: str = "default",
               model_id: str = DEFAULT_MODEL) -> bytes:
    """Synthesize `text` to PCM bytes. CosyVoice handles Mandarin natively;
    Hokkien (nan) is approximated via the Mandarin pipeline + POJ phonetic
    coaching prompt (CosyVoice supports instruction-following TTS in v2)."""
    voice = _load_cosyvoice(model_id)
    if lang == "nan":
        # CosyVoice v2 supports "instruct" mode — coach pronunciation
        prompt = f"Please speak the following Hokkien (Min Nan) sentence: {text}"
    else:
        prompt = text
    # The exact call signature depends on which CosyVoice version is loaded;
    # we keep this thin so the miner can swap to inference_sft / inference_instruct.
    audio = voice.inference_sft(prompt, speaker)
    if hasattr(audio, "tobytes"):
        return audio.tobytes()
    return bytes(audio)


@click.command()
@click.option("--text", required=True, help="Text to synthesize")
@click.option("--lang", default="zh", type=click.Choice(["zh", "nan", "yue"]))
@click.option("--out", type=click.Path(), default="cosyvoice_out.wav")
@click.option("--model", default=DEFAULT_MODEL)
def main(text: str, lang: str, out: str, model: str) -> None:
    """Render `text` to `out` via Alibaba CosyVoice. Demo wrapper."""
    click.echo(f"  loading {model}…")
    audio = synthesize(text, lang=lang, model_id=model)
    Path(out).write_bytes(audio)
    click.echo(f"  wrote {len(audio):,} bytes → {out}")


if __name__ == "__main__":
    main()
