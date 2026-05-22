"""Alibaba Qwen2-Audio miner — multimodal (audio + text) understanding.

Qwen2-Audio (Alibaba Tongyi, 2024) understands audio directly and emits
text — so a single Qwen model can serve both the **ASR** Synapse type
(audio → text) and the **MT** Synapse type (text → text) on this subnet.
It's the natural counterpart to SenseVoice for cases where you want
language understanding + transcription in one shot.

References:
  - HF: https://huggingface.co/Qwen/Qwen2-Audio-7B-Instruct
  - Card: https://github.com/QwenLM/Qwen2-Audio
"""
from __future__ import annotations

import functools
from pathlib import Path

import click

DEFAULT_MODEL = "Qwen/Qwen2-Audio-7B-Instruct"


@functools.lru_cache(maxsize=1)
def _load_qwen_audio(model_id: str = DEFAULT_MODEL):
    try:
        from transformers import AutoProcessor, Qwen2AudioForConditionalGeneration  # type: ignore
    except ImportError as e:
        raise RuntimeError(
            "transformers + Qwen2-Audio extras are not installed. "
            "Install with: pip install -e '.[miner]'"
        ) from e
    processor = AutoProcessor.from_pretrained(model_id)
    model = Qwen2AudioForConditionalGeneration.from_pretrained(
        model_id, device_map="auto"
    )
    return processor, model


def understand(audio_path: str | Path, instruction: str = "Transcribe the audio.",
               model_id: str = DEFAULT_MODEL) -> str:
    """Run Qwen2-Audio against `audio_path` with the given instruction.

    Examples of useful `instruction` values for this subnet:
      - "Transcribe the audio."
      - "Translate the audio to Mandarin."
      - "What language is the speaker using?"
    """
    import librosa  # type: ignore

    processor, model = _load_qwen_audio(model_id)
    audio, sr = librosa.load(str(audio_path), sr=processor.feature_extractor.sampling_rate)
    conversation = [
        {"role": "user", "content": [
            {"type": "audio", "audio": audio},
            {"type": "text", "text": instruction},
        ]},
    ]
    text_prompt = processor.apply_chat_template(conversation, add_generation_prompt=True, tokenize=False)
    inputs = processor(text=text_prompt, audios=[audio], sampling_rate=sr, return_tensors="pt").to(model.device)
    ids = model.generate(**inputs, max_new_tokens=256)
    out = processor.batch_decode(ids[:, inputs.input_ids.shape[-1]:], skip_special_tokens=True)
    return (out[0] if out else "").strip()


@click.command()
@click.option("--audio", required=True, type=click.Path(exists=True))
@click.option("--instruction", default="Transcribe the audio.")
@click.option("--model", default=DEFAULT_MODEL)
def main(audio: str, instruction: str, model: str) -> None:
    """Run Alibaba Qwen2-Audio on `audio` and print the response."""
    click.echo(f"  loading {model}…")
    click.echo(f"  → {understand(audio, instruction, model)}")


if __name__ == "__main__":
    main()
