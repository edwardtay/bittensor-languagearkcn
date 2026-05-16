"""One-shot CLI: bootstrap a Hokkien speaker DAO with 3 demo speakers."""
from __future__ import annotations

from pathlib import Path

import click

from .speaker_dao import SpeakerDAO


@click.command()
@click.option("--dao-path", type=click.Path(path_type=Path), default=Path("data/speaker_dao.json"))
@click.option("--lang", type=str, default="nan")
def main(dao_path: Path, lang: str) -> None:
    dao = SpeakerDAO(dao_path)
    speakers = [
        ("sp_xiamen_01", ["att_taiwan_01", "att_singapore_01", "att_penang_01"]),
        ("sp_taiwan_02", ["att_xiamen_01", "att_singapore_01", "att_penang_01"]),
        ("sp_penang_03", ["att_taiwan_01", "att_xiamen_01", "att_singapore_01"]),
    ]
    for sid, attesters in speakers:
        if not dao.is_registered(sid, lang):
            dao.register_speaker(sid, lang, stake_tao=100.0, attesters=attesters)
            click.echo(f"  ✓ registered speaker {sid} (lang={lang}, stake=100 TAO, attesters={len(attesters)})")
        else:
            click.echo(f"  · already registered: {sid}")

    # Seed a few comparison votes so Elo isn't all 1500 in the demo
    if dao.is_registered("sp_xiamen_01", lang):
        dao.record_vote("sp_xiamen_01", miner_a_uid=0, miner_b_uid=1, winner_uid=0, lang=lang)
        dao.record_vote("sp_taiwan_02", miner_a_uid=0, miner_b_uid=2, winner_uid=0, lang=lang)
        dao.record_vote("sp_penang_03", miner_a_uid=1, miner_b_uid=2, winner_uid=1, lang=lang)
        click.echo("  ✓ seeded 3 pairwise comparison votes")

    dao.save()
    click.echo(f"  ✓ DAO saved → {dao_path}\n")


if __name__ == "__main__":
    main()
