"""Validator: orchestrate the 3-signal composite score over a set of miners.

Real-network validators would (a) dendrite-query each miner over a synapse and
(b) commit-reveal their weight vector to the chain every tempo. Here we run the
*scoring* logic end-to-end against either:

  - a live miner process (default: localhost:8091)
  - or a mocked-miner JSON file (for offline demo)

and print the resulting weight vector.
"""
from __future__ import annotations

import asyncio
import json
import os
import statistics
from dataclasses import dataclass
from pathlib import Path

import click
import sacrebleu

from .glm_client import GLMClient, long_name
from .scoring import composite_score, normalize_weight_vector
from .speaker_dao import SpeakerDAO


@dataclass
class EvalSample:
    """One eval sample: a Hokkien sentence in characters/POJ and its Mandarin gloss."""

    hokkien: str       # source text (Han or POJ)
    mandarin_gold: str # gold Mandarin translation (for FLORES-style direct check)
    script: str        # "han" | "poj"


# ─── Hard-coded mini eval set (replace with FLORES-200 nan-tw rotation) ────
EVAL_SAMPLES_NAN: list[EvalSample] = [
    EvalSample(hokkien="你食飽未?", mandarin_gold="你吃饱了吗?", script="han"),
    EvalSample(hokkien="今仔日真好天。", mandarin_gold="今天天气真好。", script="han"),
    EvalSample(hokkien="我欲轉去厝。", mandarin_gold="我要回家。", script="han"),
    EvalSample(hokkien="阿母叫我食藥仔。", mandarin_gold="妈妈叫我吃药。", script="han"),
    EvalSample(hokkien="囡仔人愛讀冊。", mandarin_gold="小孩子要读书。", script="han"),
]


async def score_one_miner(
    miner_uid: int,
    miner_translations: dict[str, str],  # hokkien -> miner's mandarin
    samples: list[EvalSample],
    glm: GLMClient,
    dao: SpeakerDAO,
    lang: str = "nan",
) -> dict[str, float]:
    """Compute the three component signals and the composite for one miner.

    `miner_translations` is what the miner produced for each Hokkien input.
    """
    # ── Signal 1: Elo (cached from speaker DAO)
    elo_rating = dao.elo(miner_uid=miner_uid, lang=lang)

    # ── Signal 2: BLEU back-translation via GLM-4.6
    bleus: list[float] = []
    for s in samples:
        miner_zh = miner_translations.get(s.hokkien, "")
        if not miner_zh:
            bleus.append(0.0)
            continue
        # Round-trip: Mandarin -> back to Hokkien (via GLM), then BLEU vs original Hokkien.
        try:
            roundtrip = await glm.translate(
                miner_zh,
                src_lang=long_name("zh-Hans"),
                tgt_lang=long_name("nan"),
            )
            bleu = sacrebleu.sentence_bleu(roundtrip.translation, [s.hokkien]).score / 100.0
        except Exception as e:
            click.echo(f"  [warn] GLM back-translate failed: {e}", err=True)
            bleu = 0.0
        bleus.append(bleu)
    bleu_bt = statistics.fmean(bleus) if bleus else 0.0

    # ── Signal 3: FLORES-200 direct accuracy (here: BLEU vs gold Mandarin)
    direct_bleus: list[float] = []
    for s in samples:
        miner_zh = miner_translations.get(s.hokkien, "")
        if not miner_zh:
            direct_bleus.append(0.0)
            continue
        direct_bleus.append(
            sacrebleu.sentence_bleu(miner_zh, [s.mandarin_gold]).score / 100.0
        )
    flores = statistics.fmean(direct_bleus) if direct_bleus else 0.0

    # Clamp to [0, 1] — sacrebleu sentence_bleu can return slightly above 1.0 due to FP
    bleu_bt = max(0.0, min(1.0, bleu_bt))
    flores = max(0.0, min(1.0, flores))
    score = composite_score(elo_rating=elo_rating, bleu_bt=bleu_bt, flores=flores)

    return {
        "miner_uid": miner_uid,
        "elo_rating": score.elo_rating,
        "elo_norm": score.elo_norm,
        "bleu_bt": score.bleu_bt,
        "flores": score.flores,
        "composite": score.composite,
    }


async def main_async(
    miners_file: Path,
    netuid: int,
    lang: str,
    dao_path: Path,
) -> None:
    if not miners_file.exists():
        raise click.ClickException(f"miners file not found: {miners_file}")
    miners = json.loads(miners_file.read_text())
    # miners.json shape:
    # { "0": {"你食飽未?": "你吃饱了吗?", ...}, "1": {...} }

    api_key = os.environ.get("ZHIPU_API_KEY")
    if not api_key:
        click.echo("⚠️  ZHIPU_API_KEY not set — back-translation BLEU will be zero.", err=True)
    glm = GLMClient(api_key=api_key) if api_key else _MockGLM()

    dao = SpeakerDAO(dao_path)

    click.echo(f"\n🎯 LanguageArk-CN validator | netuid={netuid} | lang={lang} | tempo demo\n")

    results = []
    for uid_str, translations in miners.items():
        uid = int(uid_str)
        click.echo(f"  scoring miner uid={uid}…")
        r = await score_one_miner(uid, translations, EVAL_SAMPLES_NAN, glm, dao, lang=lang)
        results.append(r)

    # Weight vector
    raw = {r["miner_uid"]: r["composite"] for r in results}
    weights = normalize_weight_vector(raw)

    click.echo("\n📊 Score breakdown:\n")
    click.echo(f"{'uid':>4}  {'Elo':>7}  {'EloN':>5}  {'BLEU_bt':>8}  {'FLORES':>7}  {'composite':>9}  {'W':>6}")
    for r in sorted(results, key=lambda x: -x["composite"]):
        uid = r["miner_uid"]
        click.echo(
            f"{uid:>4}  {r['elo_rating']:>7.0f}  {r['elo_norm']:>5.2f}  "
            f"{r['bleu_bt']:>8.3f}  {r['flores']:>7.3f}  {r['composite']:>9.3f}  "
            f"{weights[uid]:>6.3f}"
        )

    # Commit-reveal: print the hash that would go on chain now
    import hashlib
    nonce = "demo-nonce-deadbeef"
    serialized = json.dumps(weights, sort_keys=True)
    commit_hash = hashlib.sha256((serialized + nonce).encode()).hexdigest()
    click.echo(f"\n🔐 commit_reveal: would submit hash now, reveal in 5 tempos")
    click.echo(f"   commit_hash = 0x{commit_hash[:32]}…")
    click.echo(f"   (anti-weight-copy: copying miners cannot see real weights for 5 tempos)\n")


class _MockGLM:
    """Stub for offline demo. Returns the input unchanged → BLEU will be low but >0."""

    async def translate(self, text, src_lang, tgt_lang):
        from types import SimpleNamespace
        return SimpleNamespace(translation=text)


@click.command()
@click.option("--miners-file", type=click.Path(exists=False, path_type=Path),
              default=Path("data/mock_miners.json"),
              help="JSON file of mock miner outputs (uid -> {hokkien: mandarin}).")
@click.option("--netuid", type=int, default=999)
@click.option("--lang", type=str, default="nan")
@click.option("--dao-path", type=click.Path(path_type=Path), default=Path("data/speaker_dao.json"))
def main(miners_file: Path, netuid: int, lang: str, dao_path: Path) -> None:
    """Run one tempo of validator scoring against mock miners."""
    asyncio.run(main_async(miners_file, netuid, lang, dao_path))


if __name__ == "__main__":
    main()
