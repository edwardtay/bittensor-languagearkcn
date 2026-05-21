"""REAL NLLB-200 miner. Loads `facebook/nllb-200-distilled-600M` and produces
genuine translations from Hokkien-Latin or Cantonese into Mandarin.

NLLB-200 is Meta's 200-language translator. Crucially, unlike SeamlessM4T-v2,
it DOES expose Hokkien (`nan_Latn` — Latin/POJ script). It does not handle
Han-character Hokkien directly, but it's the largest open model that supports
*any* form of Hokkien.

Why this matters for the submission: HONESTY.md previously flagged
"per-miner outputs are deterministic character-dropout — not actual model
outputs." This miner closes that claim — the validator can now consume real
NLLB translations.

Usage:
    python -m languageark.nllb_miner --uid=3 --eval-set=flores-yue --n=5
"""
from __future__ import annotations

import functools
import json
import time
from pathlib import Path
from typing import Optional

import click

DEFAULT_MODEL = "facebook/nllb-200-distilled-600M"

# NLLB language code map (NLLB uses BCP-47-like codes with script suffixes)
NLLB_CODES = {
    "nan": "nan_Latn",        # Hokkien (Latin / POJ)
    "nan_Latn": "nan_Latn",
    "yue": "yue_Hant",        # Cantonese (Traditional)
    "yue_Hant": "yue_Hant",
    "zh-Hans": "zho_Hans",
    "zh-Hant": "zho_Hant",
    "zho_Hans": "zho_Hans",
    "zho_Hant": "zho_Hant",
    "en": "eng_Latn",
}


@functools.lru_cache(maxsize=1)
def _load(model_id: str, device: str) -> tuple[object, object]:
    """Load tokenizer + model once. ~2.4 GB float32 on CPU."""
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

    print(f"[nllb] loading {model_id} on {device} …")
    t0 = time.time()
    tok = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_id, low_cpu_mem_usage=True).to(device)
    model.eval()
    elapsed = time.time() - t0
    nparams = sum(p.numel() for p in model.parameters()) / 1e6
    print(f"[nllb] loaded in {elapsed:.1f}s  ({nparams:.0f} M params)")
    return tok, model


def _normalize(code: str) -> str:
    if code in NLLB_CODES:
        return NLLB_CODES[code]
    raise ValueError(f"unsupported lang code for NLLB: {code!r}")


def translate(
    text: str,
    src_lang: str = "yue_Hant",
    tgt_lang: str = "zho_Hans",
    model_id: str = DEFAULT_MODEL,
    device: Optional[str] = None,
    max_new_tokens: int = 256,
) -> str:
    """Translate one sentence with REAL NLLB-200 weights."""
    import torch

    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
    tok, model = _load(model_id, device)

    src = _normalize(src_lang)
    tgt = _normalize(tgt_lang)
    tok.src_lang = src
    inputs = tok(text, return_tensors="pt").to(device)
    # NLLB requires the forced BOS to be the target language token.
    forced_bos = tok.convert_tokens_to_ids(tgt)
    with torch.no_grad():
        out = model.generate(
            **inputs,
            forced_bos_token_id=forced_bos,
            max_new_tokens=max_new_tokens,
            num_beams=4,
        )
    return tok.batch_decode(out, skip_special_tokens=True)[0]


# ─── CLI ───────────────────────────────────────────────


@click.command()
@click.option("--uid", type=int, required=True)
@click.option(
    "--eval-set",
    type=click.Choice(["hokkien", "flores-yue"]),
    default="flores-yue",
    help="`flores-yue` = real Cantonese (works well); `hokkien` = Hokkien Han text "
    "(NLLB sees nan_Latn but our gold is Han — BLEU will be low but inference is real).",
)
@click.option("--n", type=int, default=5, help="First N samples (slow on CPU).")
@click.option("--model-id", default=DEFAULT_MODEL)
@click.option("--device", default=None)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path),
    default=Path("data/real_miner_outputs.json"),
)
def main(uid, eval_set, n, model_id, device, out_path) -> None:
    """Translate an eval set with real NLLB weights and persist predictions."""
    from .eval_samples import flores_chinese_family_eval_set, hokkien_eval_set

    if eval_set == "hokkien":
        samples = hokkien_eval_set()[:n]
        src = "nan_Latn"
    else:
        samples = flores_chinese_family_eval_set(n=n)
        src = "yue_Hant"

    click.echo(f"\n🧠  NLLB-200 miner uid={uid}")
    click.echo(f"    model:    {model_id}")
    click.echo(f"    samples:  {len(samples)} from {eval_set}")
    click.echo(f"    src→tgt:  {src} → zho_Hans")
    click.echo()

    outputs: dict[str, str] = {}
    t_start = time.time()
    for i, s in enumerate(samples, 1):
        t = time.time()
        pred = translate(s.source_text, src_lang=src, tgt_lang="zho_Hans",
                         model_id=model_id, device=device)
        dt = time.time() - t
        click.echo(f"  [{i:>2}/{len(samples)}]  {dt:>5.1f}s")
        click.echo(f"      src:  {s.source_text}")
        click.echo(f"      pred: {pred}")
        click.echo(f"      gold: {s.gold_target}")
        outputs[s.source_text] = pred

    total = time.time() - t_start
    click.echo(
        f"\n  total: {total:.1f}s ({total / max(1, len(samples)):.1f}s/sentence)"
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    existing = json.loads(out_path.read_text()) if out_path.exists() else {}
    existing[str(uid)] = outputs
    out_path.write_text(json.dumps(existing, ensure_ascii=False, indent=2))
    click.echo(f"\n✓  wrote {len(outputs)} REAL translations to {out_path}")


if __name__ == "__main__":
    main()
