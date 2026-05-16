"""Validator: 3-signal composite score over a set of miners.

This is the offline-orchestration version. A real chain-deployed validator
adds `dendrite.query(axon, synapse=HokkienMT(...))` against each miner uid
and `subtensor.set_weights(...)` at the end — both are 5-line additions
once a netuid is registered (see `languageark.chain`).

Honesty:
- For Hokkien-specific scoring we use a 10-pair curated eval set (no FLORES).
- For Chinese-language-family proxy we use REAL FLORES-200 yue_Hant↔zho_Hans
  (997 sentences). Both are routed through the same composite.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import statistics
from pathlib import Path

import click

from .eval_samples import (
    EvalSample,
    flores_chinese_family_eval_set,
    generate_miner_outputs,
    hokkien_eval_set,
)
from .glm_client import GLMClient, MockGLMClient, long_name, make_glm
from .metrics import chrf_plus_plus, wer
from .scoring import composite_score, normalize_weight_vector
from .speaker_dao import SpeakerDAO


async def score_one_miner(
    miner_uid: int,
    miner_outputs: dict[str, str],
    samples: list[EvalSample],
    glm: GLMClient | MockGLMClient,
    dao: SpeakerDAO,
    lang: str = "nan",
) -> dict[str, float]:
    """Compute the 3-signal composite for one miner."""
    elo_rating = dao.elo(miner_uid=miner_uid, lang=lang)

    # ── Signal 2: BLEU/chrF back-translation via GLM
    bt_scores: list[float] = []
    for s in samples:
        pred = miner_outputs.get(s.source_text, "")
        if not pred:
            bt_scores.append(0.0)
            continue
        try:
            roundtrip = await glm.translate(
                pred,
                src_lang=long_name(s.target_lang),
                tgt_lang=long_name(s.source_lang),
            )
            bt_scores.append(chrf_plus_plus(roundtrip.translation, s.source_text))
        except Exception:
            bt_scores.append(0.0)
    bleu_bt = statistics.fmean(bt_scores) if bt_scores else 0.0

    # ── Signal 3: direct FLORES/curated reference chrF++
    direct_scores: list[float] = []
    for s in samples:
        pred = miner_outputs.get(s.source_text, "")
        direct_scores.append(chrf_plus_plus(pred, s.gold_target) if pred else 0.0)
    flores = statistics.fmean(direct_scores) if direct_scores else 0.0

    # Clamp (sacrebleu can return slight >1 due to FP)
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


async def main_async(eval_set: str, dao_path: Path) -> None:
    # 1. Pick the eval set
    if eval_set == "hokkien":
        samples = hokkien_eval_set()
        set_label = f"curated Hokkien (n={len(samples)}, no FLORES coverage)"
    elif eval_set == "flores-yue":
        samples = flores_chinese_family_eval_set(n=20)
        set_label = f"FLORES-200 yue_Hant↔zho_Hans (n={len(samples)}, real)"
    else:
        raise click.ClickException(f"unknown eval-set: {eval_set}")

    if not samples:
        raise click.ClickException(
            f"No samples available for {eval_set}. "
            "Did you fetch FLORES? See data/flores/README.md"
        )

    # 2. Synthetic miner outputs from the real samples (deterministic noise)
    all_miner_outputs = generate_miner_outputs(samples)

    # 3. GLM client (real if ZHIPU_API_KEY present, else heuristic mock)
    glm = make_glm()
    glm_kind = "GLM-4.6 (live)" if isinstance(glm, GLMClient) else "mock-heuristic (offline)"

    dao = SpeakerDAO(dao_path)

    lang = "nan" if eval_set == "hokkien" else "yue"
    click.echo(f"\n🎯 LanguageArk-CN validator")
    click.echo(f"   eval set : {set_label}")
    click.echo(f"   metric   : chrF++ (modern MT eval)")
    click.echo(f"   back-trans: {glm_kind}")
    click.echo(f"   lang     : {lang}")
    click.echo()

    results = []
    for uid, outputs in all_miner_outputs.items():
        click.echo(f"  scoring miner uid={uid}…")
        r = await score_one_miner(uid, outputs, samples, glm, dao, lang=lang)
        results.append(r)

    raw = {r["miner_uid"]: r["composite"] for r in results}
    weights = normalize_weight_vector(raw)

    click.echo("\n📊 Score breakdown:\n")
    click.echo(f"{'uid':>4}  {'Elo':>7}  {'EloN':>5}  {'BT chrF':>8}  {'chrF++':>7}  {'composite':>9}  {'W':>6}")
    for r in sorted(results, key=lambda x: -x["composite"]):
        uid = r["miner_uid"]
        click.echo(
            f"{uid:>4}  {r['elo_rating']:>7.0f}  {r['elo_norm']:>5.2f}  "
            f"{r['bleu_bt']:>8.3f}  {r['flores']:>7.3f}  {r['composite']:>9.3f}  "
            f"{weights[uid]:>6.3f}"
        )

    # WER sanity print (treats Mandarin as character stream)
    click.echo("\n📐 chrF++ vs WER for uid=2 (poor miner) sanity:")
    for s in samples[:3]:
        pred = all_miner_outputs[2].get(s.source_text, "")
        cf = chrf_plus_plus(pred, s.gold_target)
        we = wer(pred, s.gold_target)
        click.echo(f"   src={s.source_text[:18]:<18}  chrF++={cf:.3f}  WER={we:.3f}")

    # Commit-reveal
    nonce = "demo-nonce-deadbeef"
    serialized = json.dumps(weights, sort_keys=True)
    commit_hash = hashlib.sha256((serialized + nonce).encode()).hexdigest()
    click.echo(f"\n🔐 commit_reveal: submit now, reveal in 5 tempos")
    click.echo(f"   commit_hash = 0x{commit_hash[:32]}…")
    click.echo(f"   (chain wiring: bt.subtensor().commit_weights(netuid, weights, salt={nonce!r}))")


@click.command()
@click.option("--eval-set", type=click.Choice(["hokkien", "flores-yue"]),
              default="hokkien", help="Which eval corpus to score against.")
@click.option("--dao-path", type=click.Path(path_type=Path), default=Path("data/speaker_dao.json"))
def main(eval_set: str, dao_path: Path) -> None:
    """Run one tempo of validator scoring."""
    asyncio.run(main_async(eval_set, dao_path))


if __name__ == "__main__":
    main()
