"""Synapse types for LanguageArk-CN.

In a real bittensor deployment these would subclass `bittensor.Synapse`. For the
hackathon prototype we model them as pydantic types so the scoring pipeline is
testable without a chain.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

LangCode = Literal["nan", "yue", "hak", "wuu", "bo", "ug", "mn"]
"""ISO 639-3 codes we plan to support. Hokkien (`nan`) is the v1 target."""

TaskType = Literal["asr", "tts", "mt"]


class ASRSynapse(BaseModel):
    """Audio → text. Miner returns transcription in the requested target script."""

    audio_b64: str = Field(..., description="base64-encoded WAV/FLAC, 16kHz mono")
    src_lang: LangCode
    tgt_script: Literal["han", "poj", "tlpa"] = Field(
        "han",
        description=(
            "Hokkien-specific: han = Chinese characters, "
            "poj = Pe̍h-ōe-jī romanization, "
            "tlpa = Taiwanese romanization"
        ),
    )

    # Filled by miner
    transcription: str | None = None
    confidence: float | None = None


class TranslateSynapse(BaseModel):
    """Text → text translation, e.g. nan → zh-Hans or nan → en."""

    text: str
    src_lang: LangCode
    tgt_lang: str  # e.g. "zh-Hans", "en"

    # Filled by miner
    translation: str | None = None


class TTSSynapse(BaseModel):
    """Text → audio. Miner returns base64 audio of the synthesized speech."""

    text: str
    src_lang: LangCode
    voice: str | None = None

    # Filled by miner
    audio_b64: str | None = None
    sample_rate: int | None = None
