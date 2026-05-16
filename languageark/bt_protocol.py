"""REAL bittensor.Synapse subclasses for LanguageArk-CN.

These extend the actual `bittensor.Synapse` base — so a miner's `axon.attach()`
and a validator's `dendrite()` can use them with no further glue when registered
on a real netuid.

Import-graceful: we try to import the bittensor SDK; if it's unavailable (CI,
hackathon laptops without `pip install bittensor`), we fall back to pydantic-
based shims so the codebase still imports.

Run-time check: see `BT_AVAILABLE`.
"""
from __future__ import annotations

from typing import Literal

try:
    import bittensor as bt  # noqa: F401
    BT_AVAILABLE = True
    SynapseBase = bt.Synapse  # type: ignore
except ImportError:
    BT_AVAILABLE = False
    from pydantic import BaseModel as SynapseBase  # type: ignore


# ─── Shared types ───────────────────────────────────────────────

LangCode = Literal["nan", "yue", "hak", "wuu", "bo", "ug", "mn"]
HokkienScript = Literal["han", "poj", "tlpa"]


# ─── ASR synapse ────────────────────────────────────────────────

class HokkienASR(SynapseBase):
    """Hokkien audio in → text out.

    Miner side:
        axon.attach(forward_fn=transcribe, blacklist_fn=blacklist)

    Validator side:
        responses = await dendrite(
            axons=[metagraph.axons[uid] for uid in top_uids],
            synapse=HokkienASR(audio_b64=b64, target_script="han"),
            timeout=15,
        )
    """

    # Inputs
    audio_b64: str = ""
    target_script: HokkienScript = "han"

    # Outputs (filled by miner)
    transcription: str = ""
    confidence: float = 0.0


# ─── MT synapse ─────────────────────────────────────────────────

class HokkienMT(SynapseBase):
    """Hokkien text ↔ Mandarin/English text translation."""

    # Inputs
    text: str = ""
    src_lang: str = "nan"
    tgt_lang: str = "zh-Hans"

    # Output
    translation: str = ""


# ─── TTS synapse ────────────────────────────────────────────────

class HokkienTTS(SynapseBase):
    """Text → Hokkien audio (POJ or Han input)."""

    # Inputs
    text: str = ""
    voice: str = "default"

    # Output
    audio_b64: str = ""
    sample_rate: int = 16_000
