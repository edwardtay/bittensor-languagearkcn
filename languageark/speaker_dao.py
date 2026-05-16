"""Speaker DAO shim.

In production this lives on-chain (Substrate pallet or EVM contract) with stake
slashing and 2-of-3 attestation. For the hackathon prototype we model it as a
JSON-backed registry that exposes the same interface the validator needs:

    - is_registered(speaker_id, lang) -> bool
    - elo(miner_uid, lang) -> float
    - record_vote(speaker_id, miner_a, miner_b, winner, lang)
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .elo import Match, Rating, update_rating


@dataclass
class Speaker:
    speaker_id: str
    lang: str
    stake_tao: float
    attesters: list[str] = field(default_factory=list)  # 2-of-3 required
    active: bool = True


@dataclass
class MinerRating:
    miner_uid: int
    lang: str
    rating: Rating = field(default_factory=Rating)


class SpeakerDAO:
    """File-backed registry. Thread-unsafe — fine for single-process demo."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._speakers: dict[tuple[str, str], Speaker] = {}
        self._ratings: dict[tuple[int, str], MinerRating] = {}
        if self._path.exists():
            self._load()

    # ─── persistence ────────────────────────────────

    def _load(self) -> None:
        raw = json.loads(self._path.read_text())
        for s in raw.get("speakers", []):
            sp = Speaker(**s)
            self._speakers[(sp.speaker_id, sp.lang)] = sp
        for r in raw.get("ratings", []):
            rating = Rating(**r["rating"])
            self._ratings[(r["miner_uid"], r["lang"])] = MinerRating(
                miner_uid=r["miner_uid"], lang=r["lang"], rating=rating
            )

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps({
            "speakers": [asdict(s) for s in self._speakers.values()],
            "ratings": [
                {"miner_uid": mr.miner_uid, "lang": mr.lang, "rating": asdict(mr.rating)}
                for mr in self._ratings.values()
            ],
        }, indent=2, ensure_ascii=False))

    # ─── registration (2-of-3 attestation gate) ─────

    def register_speaker(
        self,
        speaker_id: str,
        lang: str,
        stake_tao: float,
        attesters: list[str],
    ) -> Speaker:
        if stake_tao < 100.0:
            raise ValueError(f"Min stake is 100 TAO, got {stake_tao}")
        if len(set(attesters)) < 2:
            raise ValueError("Need at least 2 distinct attesters")
        sp = Speaker(speaker_id=speaker_id, lang=lang, stake_tao=stake_tao, attesters=attesters)
        self._speakers[(speaker_id, lang)] = sp
        return sp

    def is_registered(self, speaker_id: str, lang: str) -> bool:
        sp = self._speakers.get((speaker_id, lang))
        return sp is not None and sp.active

    # ─── ratings ────────────────────────────────────

    def elo(self, miner_uid: int, lang: str) -> float:
        return self._rating_for(miner_uid, lang).rating.rating

    def _rating_for(self, miner_uid: int, lang: str) -> MinerRating:
        key = (miner_uid, lang)
        if key not in self._ratings:
            self._ratings[key] = MinerRating(miner_uid=miner_uid, lang=lang)
        return self._ratings[key]

    def record_vote(
        self,
        speaker_id: str,
        miner_a_uid: int,
        miner_b_uid: int,
        winner_uid: int | None,
        lang: str,
    ) -> None:
        """A speaker compares miner_a vs miner_b. winner_uid=None means draw."""
        if not self.is_registered(speaker_id, lang):
            raise PermissionError(f"Speaker {speaker_id} not registered for {lang}")

        mr_a = self._rating_for(miner_a_uid, lang)
        mr_b = self._rating_for(miner_b_uid, lang)

        if winner_uid == miner_a_uid:
            outcome_a, outcome_b = 1.0, 0.0
        elif winner_uid == miner_b_uid:
            outcome_a, outcome_b = 0.0, 1.0
        elif winner_uid is None:
            outcome_a = outcome_b = 0.5
        else:
            raise ValueError(f"winner_uid {winner_uid} must be one of {miner_a_uid}, {miner_b_uid}, or None")

        new_a = update_rating(mr_a.rating, [Match(mr_b.rating.rating, mr_b.rating.rd, outcome_a)])
        new_b = update_rating(mr_b.rating, [Match(mr_a.rating.rating, mr_a.rating.rd, outcome_b)])
        mr_a.rating = new_a
        mr_b.rating = new_b
