"""Alibaba SenseVoice ASR miner — speech audio → text.

SenseVoice (2024) is Alibaba's open-source multilingual ASR model from the
FunAudioLLM family. Designed for low-latency Chinese-family ASR with
emotion / event tagging. Public weights on HF / ModelScope.

We wire it as the **default ASR miner backend** for the LanguageArk-CN
subnet. SenseVoice covers Mandarin, Cantonese, Min Nan / Hokkien (`nan`),
Hakka, Wu — i.e. the entire v1 language wedge of this subnet — in a
single model. This is exactly the sponsor-stack alignment we want.

References:
  - HF: https://huggingface.co/FunAudioLLM/SenseVoiceSmall
  - Repo: https://github.com/FunAudioLLM/SenseVoice
"""
from __future__ import annotations

import functools
from pathlib import Path
from typing import Optional

import click

DEFAULT_MODEL = "FunAudioLLM/SenseVoiceSmall"


@functools.lru_cache(maxsize=1)
def _load_sensevoice(model_id: str = DEFAULT_MODEL):
    """Lazy-load SenseVoice via FunASR. Requires the `funasr` extras."""
    try:
        from funasr import AutoModel  # type: ignore
    except ImportError as e:
        raise RuntimeError(
            "FunASR is not installed. Install with: pip install funasr "
            "(or follow https://github.com/FunAudioLLM/SenseVoice)"
        ) from e
    return AutoModel(model=model_id, trust_remote_code=False)


# SenseVoice supports the languages we care about for v1
SENSEVOICE_LANGS = {"zh": "zh", "yue": "yue", "nan": "nan", "hak": "hak", "en": "en", "auto": "auto"}


def transcribe(audio_path: str | Path, *, lang: str = "auto",
               model_id: str = DEFAULT_MODEL) -> str:
    """Transcribe `audio_path` to text. `lang='auto'` lets SenseVoice
    detect; pass an explicit code (`nan`, `yue`, `zh`) to force a path."""
    model = _load_sensevoice(model_id)
    out = model.generate(
        input=str(audio_path),
        language=SENSEVOICE_LANGS.get(lang, "auto"),
        use_itn=True,
    )
    if isinstance(out, list) and out:
        return out[0].get("text", "").strip()
    if isinstance(out, dict):
        return out.get("text", "").strip()
    return ""


@click.command()
@click.option("--audio", required=True, type=click.Path(exists=True),
              help="WAV / FLAC / MP3 to transcribe")
@click.option("--lang", default="auto",
              type=click.Choice(list(SENSEVOICE_LANGS.keys())))
@click.option("--model", default=DEFAULT_MODEL)
def main(audio: str, lang: str, model: str) -> None:
    """Run Alibaba SenseVoice ASR on `audio` and print the transcript."""
    click.echo(f"  loading {model}…")
    text = transcribe(audio, lang=lang, model_id=model)
    click.echo(f"  {lang}: {text}")


if __name__ == "__main__":
    main()
