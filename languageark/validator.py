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
from .glm_client import Judge, long_name, make_glm
from .metrics import chrf_plus_plus, wer
from .scoring import composite_score, normalize_weight_vector
from .speaker_dao import SpeakerDAO


async def score_one_miner(
    miner_uid: int,
    miner_outputs: dict[str, str],
    samples: list[EvalSample],
    glm: Judge,
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


def _make_dao(backend: str, json_path: Path, rpc_url: str, contract_address: str | None):
    """Build the speaker DAO the validator scores against.

    backend='json'    → file-backed SpeakerDAO (default, used in unit tests + demo).
    backend='onchain' → OnChainSpeakerDAO talking to a deployed Solidity contract.
    """
    if backend == "json":
        return SpeakerDAO(json_path)
    if backend == "onchain":
        from .speaker_dao_chain import OnChainSpeakerDAO, connect
        if not contract_address:
            raise click.ClickException(
                "--dao-contract is required when --dao-backend=onchain"
            )
        w3 = connect(rpc_url)
        return OnChainSpeakerDAO(w3, contract_address)
    raise click.ClickException(f"unknown dao backend: {backend!r}")


async def main_async(
    eval_set: str,
    dao_path: Path,
    dao_backend: str,
    dao_rpc: str,
    dao_contract: str | None,
) -> None:
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

    # 2. Synthetic miner outputs from the real samples (deterministic noise) +
    #    optional REAL miner outputs from disk (e.g. Claude / NLLB miners).
    all_miner_outputs = generate_miner_outputs(samples)
    real_path = Path("data/real_miner_outputs.json")
    if real_path.exists():
        loaded = json.loads(real_path.read_text())
        for uid_str, preds in loaded.items():
            uid = int(uid_str)
            if any(s.source_text in preds for s in samples):
                all_miner_outputs[uid] = preds
                click.echo(f"   + loaded REAL miner uid={uid} from {real_path} "
                           f"({len(preds)} predictions)")

    # 3. LLM judge — picks best available (Chinese models first, then Claude, then mock)
    glm = make_glm()
    glm_kind = glm.label

    dao = _make_dao(dao_backend, dao_path, dao_rpc, dao_contract)
    dao_label = (
        f"on-chain @ {dao_contract[:10]}…  (RPC {dao_rpc})"
        if dao_backend == "onchain" else f"json @ {dao_path}"
    )

    lang = "nan" if eval_set == "hokkien" else "yue"
    click.echo(f"\n🎯 LanguageArk-CN validator")
    click.echo(f"   eval set : {set_label}")
    click.echo(f"   metric   : chrF++ (modern MT eval)")
    click.echo(f"   back-trans: {glm_kind}")
    click.echo(f"   dao      : {dao_label}")
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
@click.option("--dao-backend", type=click.Choice(["json", "onchain"]), default="json",
              help="`json` = file-backed shim (default); `onchain` = deployed Solidity contract.")
@click.option("--dao-rpc", default="http://127.0.0.1:8545",
              help="EVM RPC URL when --dao-backend=onchain.")
@click.option("--dao-contract", default=None,
              help="Deployed SpeakerDAO address (required when --dao-backend=onchain).")
def main(eval_set: str, dao_path: Path, dao_backend: str, dao_rpc: str, dao_contract: str | None) -> None:
    """Run one tempo of validator scoring."""
    asyncio.run(main_async(eval_set, dao_path, dao_backend, dao_rpc, dao_contract))


if __name__ == "__main__":
    main()
