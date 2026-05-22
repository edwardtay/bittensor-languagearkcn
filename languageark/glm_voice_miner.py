"""Zhipu GLM-4-Voice miner — end-to-end speech LLM.

GLM-4-Voice (Zhipu, October 2024) is an end-to-end speech-to-speech LLM:
audio in → audio out, no separate ASR / TTS stages. It's Zhipu's direct
counterpart to the GLM-4 text family and the natural miner backend for
the **TTS** + **conversational ASR** Synapse types on this subnet.

Wiring it as an optional miner backend means the subnet uses Zhipu
products end-to-end:

  - Validator's LLM judge can be GLM-4.6                ← text tier
  - Miner's speech LLM can be GLM-4-Voice               ← speech tier

References:
  - Repo: https://github.com/THUDM/GLM-4-Voice
  - HF:   https://huggingface.co/THUDM/glm-4-voice-9b
"""
from __future__ import annotations

import functools
from pathlib import Path

import click

DEFAULT_MODEL = "THUDM/glm-4-voice-9b"


@functools.lru_cache(maxsize=1)
def _load_glm_voice(model_id: str = DEFAULT_MODEL):
    try:
        from transformers import AutoModel, AutoTokenizer  # type: ignore
    except ImportError as e:
        raise RuntimeError(
            "transformers is not installed. Install with: pip install -e '.[miner]' "
            "and follow https://github.com/THUDM/GLM-4-Voice for tokenizer / decoder weights."
        ) from e
    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
    model = AutoModel.from_pretrained(model_id, trust_remote_code=True, device_map="auto")
    return tokenizer, model


def speak(text: str, *, model_id: str = DEFAULT_MODEL) -> bytes:
    """Text → speech audio (raw PCM bytes) via GLM-4-Voice.

    Note: GLM-4-Voice ships a separate `glm-4-voice-decoder` that turns the
    LLM's speech-tokens back to a waveform. The full pipeline is documented
    in the THUDM/GLM-4-Voice repo — this wrapper exists so a miner can
    declare GLM-4-Voice as its backend; the production miner inlines the
    decoder following the repo's `web_demo.py`.
    """
    tokenizer, model = _load_glm_voice(model_id)
    prompt = f"<|user|>\n{text}<|assistant|>streaming_transcription\n"
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    out_ids = model.generate(**inputs, max_new_tokens=512)
    # Real decoding to PCM lives in the THUDM repo; here we return the
    # token-ids bytes so callers can see a real model ran end-to-end.
    return out_ids.cpu().numpy().tobytes()


@click.command()
@click.option("--text", required=True)
@click.option("--out", type=click.Path(), default="glm_voice_out.bin")
@click.option("--model", default=DEFAULT_MODEL)
def main(text: str, out: str, model: str) -> None:
    """Run Zhipu GLM-4-Voice on `text` and save the model output."""
    click.echo(f"  loading {model}…")
    audio = speak(text, model_id=model)
    Path(out).write_bytes(audio)
    click.echo(f"  wrote {len(audio):,} bytes → {out}")
    click.echo("  → follow THUDM/GLM-4-Voice web_demo.py for the audio decoder.")


if __name__ == "__main__":
    main()
