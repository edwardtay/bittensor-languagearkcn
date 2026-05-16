"""Reference miner.

For the hackathon prototype we ship a thin wrapper that can run in two modes:

  --mode=mock    (default) — read translations from a JSON file. Zero deps.
  --mode=whisper            — load a Hokkien Whisper fine-tune (extras: [miner])

The mock mode is what we'll demo if hardware is iffy on the judging floor.
Real-network miners would serve over an axon; here we just print outputs.
"""
from __future__ import annotations

import json
from pathlib import Path

import click


DEFAULT_MOCK_OUTPUTS = {
    "你食飽未?": "你吃饱了吗?",
    "今仔日真好天。": "今天天气真好。",
    "我欲轉去厝。": "我要回家。",
    "阿母叫我食藥仔。": "妈妈叫我吃药。",
    "囡仔人愛讀冊。": "小孩子要读书。",
}


def run_mock(uid: int, out_path: Path) -> None:
    """Write a JSON of {uid: {hokkien: mandarin}} that validator.py can consume."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    existing = json.loads(out_path.read_text()) if out_path.exists() else {}
    existing[str(uid)] = DEFAULT_MOCK_OUTPUTS
    out_path.write_text(json.dumps(existing, ensure_ascii=False, indent=2))
    click.echo(f"✓ miner uid={uid} wrote {len(DEFAULT_MOCK_OUTPUTS)} translations to {out_path}")


def run_whisper(uid: int, out_path: Path) -> None:
    """Real path: load a Hokkien Whisper model and translate audio samples.

    Lazy import so the mock mode has zero ML deps.
    """
    try:
        from transformers import WhisperForConditionalGeneration, WhisperProcessor  # type: ignore
        import torch  # type: ignore  # noqa: F401
    except ImportError as e:
        raise click.ClickException(
            "Whisper mode needs extras: `uv sync --extra miner` (or `pip install .[miner]`)"
        ) from e

    # Placeholder — in the real demo we'd load e.g.
    #   "openai/whisper-small" + a Hokkien LoRA from HF Hub
    # and decode audio samples drawn from Common Voice nan-tw.
    click.echo("[whisper] not yet wired — falling back to mock outputs")
    run_mock(uid, out_path)


@click.command()
@click.option("--uid", type=int, required=True, help="This miner's uid on the netuid")
@click.option("--lang", type=str, default="nan", help="ISO 639-3 language code")
@click.option("--mode", type=click.Choice(["mock", "whisper"]), default="mock")
@click.option("--out", "out_path", type=click.Path(path_type=Path),
              default=Path("data/mock_miners.json"))
def main(uid: int, lang: str, mode: str, out_path: Path) -> None:
    """Run a miner and write its outputs where the validator can pick them up."""
    if lang != "nan":
        raise click.ClickException(f"v1 demo only supports lang=nan (Hokkien); got {lang}")
    if mode == "mock":
        run_mock(uid, out_path)
    else:
        run_whisper(uid, out_path)


if __name__ == "__main__":
    main()
