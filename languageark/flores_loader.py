"""Load real FLORES-200 parallel data.

IMPORTANT HONESTY NOTE: FLORES-200 does NOT include Hokkien / Min Nan.
The 200 languages cover yue_Hant (Cantonese) and min_Latn (Minangkabau, which
is a Sumatran language unrelated to Min Nan). This is itself a market signal —
even the de-facto multilingual eval corpus skips Hokkien.

What we do here:
- Load REAL `yue_Hant` ↔ `zho_Hans` pairs (997 dev sentences, professional translators)
  → use as a "Chinese-language-family" proxy evaluation
- Maintain a curated Hokkien sub-corpus (`HOKKIEN_PAIRS` below) that the subnet
  itself bootstraps and grows over time

Files live under `data/flores/`, fetched once from:
  https://dl.fbaipublicfiles.com/nllb/flores200_dataset.tar.gz
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


FLORES_DIR = Path(__file__).resolve().parent.parent / "data" / "flores"


@dataclass(frozen=True)
class FloresPair:
    """One parallel sentence pair from FLORES-200."""

    idx: int
    src_text: str        # source language (e.g. yue_Hant)
    tgt_text: str        # target language (e.g. zho_Hans)
    src_lang: str
    tgt_lang: str


def _read_lines(path: Path) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(
            f"FLORES file missing at {path}. "
            "Run: curl -O https://dl.fbaipublicfiles.com/nllb/flores200_dataset.tar.gz "
            "and extract dev/yue_Hant.dev + dev/zho_Hans.dev into data/flores/."
        )
    return [line.rstrip("\n") for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


@lru_cache(maxsize=4)
def load_flores_pairs(
    src_lang: str = "yue_Hant",
    tgt_lang: str = "zho_Hans",
    split: str = "dev",
) -> list[FloresPair]:
    """Load parallel sentence pairs from local FLORES files.

    Default loads Cantonese ↔ Simplified Mandarin (`yue_Hant.dev` / `zho_Hans.dev`).
    Both files have 997 sentences in identical order.
    """
    src_path = FLORES_DIR / f"{src_lang}.{split}"
    tgt_path = FLORES_DIR / f"{tgt_lang}.{split}"
    src_lines = _read_lines(src_path)
    tgt_lines = _read_lines(tgt_path)
    if len(src_lines) != len(tgt_lines):
        raise ValueError(
            f"FLORES mismatch: {src_lang} has {len(src_lines)} lines, {tgt_lang} has {len(tgt_lines)}"
        )
    return [
        FloresPair(idx=i, src_text=s, tgt_text=t, src_lang=src_lang, tgt_lang=tgt_lang)
        for i, (s, t) in enumerate(zip(src_lines, tgt_lines))
    ]


def is_available() -> bool:
    """Cheap check before importing the heavy eval pipeline."""
    return (FLORES_DIR / "yue_Hant.dev").exists() and (FLORES_DIR / "zho_Hans.dev").exists()


# ─── Hokkien-specific curated set (the gap FLORES doesn't cover) ──────

@dataclass(frozen=True)
class HokkienPair:
    hokkien_han: str   # Hokkien in Han characters (Taiwanese standard)
    poj: str           # Pe̍h-ōe-jī romanization
    mandarin: str      # Simplified Mandarin gold

# These are real Hokkien sentences in use today; sources include the Taiwan
# Ministry of Education Hokkien dictionary (教育部臺灣閩南語常用詞辭典) and
# documented usage in Hokkien diaspora communities. We grow this set via the
# subnet's own speaker-DAO workflow — that's the product.
HOKKIEN_PAIRS: list[HokkienPair] = [
    HokkienPair("你食飽未?", "lí chia̍h-pá-bē?", "你吃饱了吗?"),
    HokkienPair("今仔日真好天。", "kin-á-ji̍t chin hó-thiⁿ.", "今天天气真好。"),
    HokkienPair("我欲轉去厝。", "góa beh tńg-khì chhù.", "我要回家。"),
    HokkienPair("阿母叫我食藥仔。", "a-bú kiò góa chia̍h io̍h-á.", "妈妈叫我吃药。"),
    HokkienPair("囡仔人愛讀冊。", "gín-á-lâng ài tha̍k chheh.", "小孩子要读书。"),
    HokkienPair("這碗麵真好食。", "chit óaⁿ mī chin hó-chia̍h.", "这碗面真好吃。"),
    HokkienPair("阿公的腳手猶閣真𠢕。", "a-kong ê kha-chhiú iáu-koh chin gâu.", "爷爷的手脚还很灵活。"),
    HokkienPair("明仔載欲去揣朋友。", "bîn-á-chài beh khì chhōe pêng-iú.", "明天要去找朋友。"),
    HokkienPair("我欲食一寡水果。", "góa beh chia̍h chi̍t-kóa chúi-kó.", "我想吃一些水果。"),
    HokkienPair("這個學生真𠢕讀冊。", "chit-ê ha̍k-seng chin gâu tha̍k-chheh.", "这个学生很会读书。"),
]
