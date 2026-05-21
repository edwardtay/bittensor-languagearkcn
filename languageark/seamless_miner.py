"""REAL SeamlessM4T-v2 miner — and an honest finding.

We empirically probed the tokenizer of `facebook/seamless-m4t-v2-large`:

    >>> [k for k in vocab if k in ('__cmn__', '__cmn_Hant__', '__yue__', '__nan__')]
    ['__cmn__', '__cmn_Hant__', '__yue__']    # NO __nan__

→ Meta's flagship multilingual model **does not actually support Hokkien text
translation** in v2-large. (Meta's separate `m4t_hokkien` Fairseq model from
2022 handles Hokkien speech-to-speech but is not in the HF transformers library.)

This finding is itself the strongest possible market signal for LanguageArk-CN:
the dominant open multilingual model skips Hokkien. The subnet's purpose is to
build the data, the speakers, and the incentive structure that close this gap.

What this module actually does, end-to-end with real weights loaded:

  1. Cantonese ↔ Mandarin (yue → cmn) — REAL, using SeamlessM4T-v2-large.
     We run this against real FLORES-200 yue_Hant/zho_Hans pairs.
  2. Hokkien → Mandarin (nan → cmn) — falls back, because the model has no
     `__nan__` token. We surface this gap loudly in the output rather than
     pretending it works.

References:
  - HF: https://huggingface.co/facebook/seamless-m4t-v2-large
  - Meta Hokkien S2ST (separate model): https://about.fb.com/news/2022/10/hokkien-ai-speech-translation/
  - Confirming language list: https://github.com/facebookresearch/seamless_communication
"""
from __future__ import annotations

import functools
import json
import time
from pathlib import Path
from typing import Optional

import click

DEFAULT_MODEL = "facebook/seamless-m4t-v2-large"
HOKKIEN_SEAMLESS_FALLBACK = "yue"   # Cantonese — closest supported relative
MANDARIN = "cmn"

# Public ISO/SeamlessM4T language code constants (used by tests + callers).
SEAMLESS_HOKKIEN = "nan"
SEAMLESS_MANDARIN = "cmn"
SEAMLESS_CANTONESE = "yue"

# Confirmed at runtime by `_check_lang_support()`
SUPPORTED_LANGS: set[str] | None = None


@functools.lru_cache(maxsize=1)
def _load(model_id: str, device: str) -> tuple[object, object, set[str]]:
    """Load processor + model once. Also probe the language tokens."""
    from transformers import AutoProcessor, SeamlessM4Tv2ForTextToText
    import torch
    import re

    print(f"[seamless] loading {model_id} on {device} …")
    t0 = time.time()
    proc = AutoProcessor.from_pretrained(model_id)
    dtype = torch.float16 if device == "cuda" else torch.float32
    model = SeamlessM4Tv2ForTextToText.from_pretrained(
        model_id,
        torch_dtype=dtype,
        low_cpu_mem_usage=True,
    ).to(device)
    model.eval()
    elapsed = time.time() - t0
    nparams = sum(p.numel() for p in model.parameters()) / 1e9
    print(f"[seamless] loaded in {elapsed:.1f}s ({nparams:.2f}B params)")

    # Probe lang support
    vocab = proc.tokenizer.get_vocab()
    langs = {re.match(r"__([a-z]{3}(?:_[A-Z][a-z]+)?)__$", k).group(1)
             for k in vocab if re.match(r"__[a-z]{3}(?:_[A-Z][a-z]+)?__$", k)}
    print(f"[seamless] {len(langs)} language codes supported")
    if "nan" not in langs:
        print("[seamless] ⚠️  Hokkien (nan) NOT in tokenizer — this is the LanguageArk-CN gap.")
    return proc, model, langs


def _normalize_lang(code: str, supported: set[str]) -> tuple[str, str]:
    """Map our ISO code → SeamlessM4T code; return (used, note).

    note is non-empty when we had to substitute.
    """
    if code in supported:
        return code, ""
    if code == "nan":
        # Hokkien: fall back to Cantonese with a loud note
        return HOKKIEN_SEAMLESS_FALLBACK, (
            f"Hokkien (nan) unsupported by SeamlessM4T-v2 — "
            f"falling back to {HOKKIEN_SEAMLESS_FALLBACK} (Cantonese). "
            "This is the LanguageArk-CN gap."
        )
    if code in ("zh-Hans", "zho_Hans"):
        return "cmn", ""
    if code in ("zh-Hant", "zho_Hant"):
        return "cmn_Hant", ""
    if code in ("yue_Hant", "yue_Hans"):
        return "yue", ""
    return code, f"unrecognized code {code!r}, passing through"


def translate(
    text: str,
    src_lang: str = "yue",
    tgt_lang: str = MANDARIN,
    model_id: str = DEFAULT_MODEL,
    device: Optional[str] = None,
    max_new_tokens: int = 256,
) -> str:
    """Translate one sentence using REAL SeamlessM4T-v2 weights."""
    import torch
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
    proc, model, supported = _load(model_id, device)

    src_used, src_note = _normalize_lang(src_lang, supported)
    tgt_used, tgt_note = _normalize_lang(tgt_lang, supported)
    for note in (src_note, tgt_note):
        if note:
            print(f"[seamless] {note}")

    inputs = proc(text=text, src_lang=src_used, return_tensors="pt").to(device)
    with torch.no_grad():
        out = model.generate(**inputs, tgt_lang=tgt_used, max_new_tokens=max_new_tokens)
    return proc.decode(out[0].tolist(), skip_special_tokens=True)


def translate_batch(
    texts: list[str],
    src_lang: str = "yue",
    tgt_lang: str = MANDARIN,
    model_id: str = DEFAULT_MODEL,
    device: Optional[str] = None,
) -> list[str]:
    return [translate(t, src_lang, tgt_lang, model_id, device) for t in texts]


# ─── CLI ───────────────────────────────────────────────

@click.command()
@click.option("--uid", type=int, required=True)
@click.option("--lang", type=click.Choice(["nan", "yue"]), default="yue",
              help="`yue` = real Cantonese (works); `nan` = Hokkien (will fall back & note).")
@click.option("--eval-set", type=click.Choice(["hokkien", "flores-yue"]), default="flores-yue",
              help="Which corpus to translate.")
@click.option("--n", type=int, default=3, help="Only process first N samples (model is slow on CPU).")
@click.option("--model-id", default=DEFAULT_MODEL)
@click.option("--device", default=None)
@click.option("--out", "out_path", type=click.Path(path_type=Path),
              default=Path("data/mock_miners.json"))
def main(uid, lang, eval_set, n, model_id, device, out_path) -> None:
    """Run SeamlessM4T-v2 on a real eval set and write predictions."""
    from .eval_samples import flores_chinese_family_eval_set, hokkien_eval_set

    if eval_set == "hokkien":
        samples = hokkien_eval_set()[:n]
        src_lang = "nan"  # honest: will fall back
    else:
        samples = flores_chinese_family_eval_set(n=n)
        src_lang = "yue_Hant"

    click.echo(f"\n🎙️  SeamlessM4T-v2 miner uid={uid}")
    click.echo(f"    model:    {model_id}")
    click.echo(f"    samples:  {len(samples)} from {eval_set}")
    click.echo(f"    src→tgt:  {src_lang} → zho_Hans (cmn)")
    click.echo()

    outputs: dict[str, str] = {}
    t_start = time.time()
    for i, s in enumerate(samples, 1):
        t = time.time()
        pred = translate(s.source_text, src_lang=src_lang, tgt_lang="cmn",
                          model_id=model_id, device=device)
        dt = time.time() - t
        click.echo(f"  [{i:>2}/{len(samples)}] {dt:>5.1f}s")
        click.echo(f"      src: {s.source_text}")
        click.echo(f"      pred: {pred}")
        click.echo(f"      gold: {s.gold_target}")
        outputs[s.source_text] = pred

    click.echo(f"\n  total: {time.time() - t_start:.1f}s "
               f"({(time.time() - t_start) / max(1, len(samples)):.1f}s/sentence)")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    existing = json.loads(out_path.read_text()) if out_path.exists() else {}
    existing[str(uid)] = outputs
    out_path.write_text(json.dumps(existing, ensure_ascii=False, indent=2))
    click.echo(f"\n✓ wrote {len(outputs)} translations to {out_path}")


if __name__ == "__main__":
    main()
