"""REAL Claude miner: produces actual ML translations as a miner output.

Closes the HONESTY.md gap "per-miner outputs are deterministic character-dropout
of the gold reference — NOT actual model outputs." This miner is a genuine
LLM doing the work — Claude Haiku 4.5 translating Hokkien (or Cantonese) into
Mandarin. The validator scores its predictions against the FLORES gold the
same way it scores any other miner.

This is also a useful real-world point for the demo: miners on LanguageArk-CN
can be anything — LLM-as-translator, distilled Whisper, fine-tuned NLLB. The
incentive layer (Elo + back-translation + held-out chrF++) discriminates by
output quality, not by what produced it.

Usage:
    export ANTHROPIC_API_KEY=...
    python -m languageark.claude_miner --uid=3 --eval-set=hokkien --n=5
"""
from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from typing import Optional

import click

DEFAULT_MODEL = "claude-haiku-4-5-20251001"


async def _translate_one(
    client,
    text: str,
    src_long: str,
    tgt_long: str,
    *,
    model: str,
) -> str:
    prompt = (
        f"Translate the following text from {src_long} into {tgt_long}. "
        f"Output ONLY the translation in {tgt_long} — no quotes, no commentary, "
        f"no English, no romanization, no explanation. Preserve register and "
        f"proper nouns.\n\nSource: {text}"
    )
    resp = await client.messages.create(
        model=model,
        max_tokens=512,
        temperature=0.0,
        messages=[{"role": "user", "content": prompt}],
    )
    parts = [b.text for b in resp.content if getattr(b, "type", None) == "text"]
    return ("".join(parts)).strip()


async def translate_samples(samples, model: str = DEFAULT_MODEL) -> dict[str, str]:
    """Translate every sample.source_text → predicted target_lang via Claude."""
    from anthropic import AsyncAnthropic

    from .glm_client import long_name

    client = AsyncAnthropic()
    out: dict[str, str] = {}
    for i, s in enumerate(samples, 1):
        src_long = long_name(s.source_lang)
        tgt_long = long_name(s.target_lang)
        t = time.time()
        pred = await _translate_one(client, s.source_text, src_long, tgt_long, model=model)
        dt = time.time() - t
        click.echo(f"  [{i:>2}/{len(samples)}]  {dt:>4.1f}s   {s.source_text[:32]:<32}  →  {pred[:48]}")
        out[s.source_text] = pred
    return out


@click.command()
@click.option("--uid", type=int, required=True)
@click.option("--eval-set", type=click.Choice(["hokkien", "flores-yue"]), default="hokkien")
@click.option("--n", type=int, default=5, help="Number of samples to translate.")
@click.option("--model", default=DEFAULT_MODEL)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path),
    default=Path("data/real_miner_outputs.json"),
)
def main(uid: int, eval_set: str, n: int, model: str, out_path: Path) -> None:
    """Translate a real eval set via Claude and persist real miner predictions."""
    from .eval_samples import flores_chinese_family_eval_set, hokkien_eval_set

    if eval_set == "hokkien":
        samples = hokkien_eval_set()[:n]
    else:
        samples = flores_chinese_family_eval_set(n=n)

    click.echo(f"\n🧠  Claude miner uid={uid}")
    click.echo(f"    model:    {model}")
    click.echo(f"    samples:  {len(samples)} from {eval_set}")
    click.echo(f"    src→tgt:  {samples[0].source_lang} → {samples[0].target_lang}")
    click.echo()

    t0 = time.time()
    outputs = asyncio.run(translate_samples(samples, model=model))
    total = time.time() - t0
    click.echo(f"\n  total: {total:.1f}s ({total / max(1, len(samples)):.1f}s/sentence)")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    existing = json.loads(out_path.read_text()) if out_path.exists() else {}
    existing[str(uid)] = outputs
    out_path.write_text(json.dumps(existing, ensure_ascii=False, indent=2))
    click.echo(f"\n✓  wrote {len(outputs)} REAL Claude translations to {out_path}")


if __name__ == "__main__":
    main()
