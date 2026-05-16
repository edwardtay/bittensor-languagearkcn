"""Hokkien evaluation samples + per-miner mock outputs of varying quality.

These come from real Hokkien usage (Han + POJ co-existence). Source sentences
are common everyday Hokkien; gold Mandarin is the standard translation.

For the v0 demo we ship three miner profiles to differentiate scoring:

  uid=0  professional   — accurate, native-quality Mandarin
  uid=1  competent      — minor word-choice / register issues
  uid=2  poor           — literal/wrong glosses, drops particles
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EvalSample:
    hokkien: str         # source Hokkien (Han characters)
    poj: str             # Pe̍h-ōe-jī romanization
    mandarin_gold: str   # standard Mandarin translation


EVAL_SAMPLES_NAN: list[EvalSample] = [
    EvalSample(
        hokkien="你食飽未?",
        poj="lí chia̍h-pá-bē?",
        mandarin_gold="你吃饱了吗?",
    ),
    EvalSample(
        hokkien="今仔日真好天。",
        poj="kin-á-ji̍t chin hó-thiⁿ.",
        mandarin_gold="今天天气真好。",
    ),
    EvalSample(
        hokkien="我欲轉去厝。",
        poj="góa beh tńg-khì chhù.",
        mandarin_gold="我要回家。",
    ),
    EvalSample(
        hokkien="阿母叫我食藥仔。",
        poj="a-bú kiò góa chia̍h io̍h-á.",
        mandarin_gold="妈妈叫我吃药。",
    ),
    EvalSample(
        hokkien="囡仔人愛讀冊。",
        poj="gín-á-lâng ài tha̍k chheh.",
        mandarin_gold="小孩子要读书。",
    ),
    EvalSample(
        hokkien="這碗麵真好食。",
        poj="chit óaⁿ mī chin hó-chia̍h.",
        mandarin_gold="这碗面真好吃。",
    ),
    EvalSample(
        hokkien="阿公的腳手猶閣真𠢕。",
        poj="a-kong ê kha-chhiú iáu-koh chin gâu.",
        mandarin_gold="爷爷的手脚还很灵活。",
    ),
    EvalSample(
        hokkien="明仔載欲去揣朋友。",
        poj="bîn-á-chài beh khì chhōe pêng-iú.",
        mandarin_gold="明天要去找朋友。",
    ),
]


# Per-miner outputs — Hokkien source → Mandarin attempt
# uid=0: high quality; matches gold ~exactly
MINER_0_OUTPUTS: dict[str, str] = {
    s.hokkien: s.mandarin_gold for s in EVAL_SAMPLES_NAN
}

# uid=1: competent but with minor swaps (register / synonyms)
MINER_1_OUTPUTS: dict[str, str] = {
    "你食飽未?": "你吃饱没有?",
    "今仔日真好天。": "今天天气好。",
    "我欲轉去厝。": "我想回家。",
    "阿母叫我食藥仔。": "妈妈让我吃药。",
    "囡仔人愛讀冊。": "孩子要读书。",
    "這碗麵真好食。": "这碗面好吃。",
    "阿公的腳手猶閣真𠢕。": "爷爷手脚还很厉害。",
    "明仔載欲去揣朋友。": "明天要找朋友。",
}

# uid=2: poor — literal glosses, wrong words, drops particles
MINER_2_OUTPUTS: dict[str, str] = {
    "你食飽未?": "你食饱未。",                              # transliterated, ungrammatical
    "今仔日真好天。": "今天真好天空。",                       # mistranslates 好天
    "我欲轉去厝。": "我要转去房子。",                         # 厝 ≠ 房子 in register
    "阿母叫我食藥仔。": "阿母叫我食药。",                     # leaves 阿母 untranslated
    "囡仔人愛讀冊。": "孩子人爱读册。",                       # wrong word for 冊
    "這碗麵真好食。": "这碗面真好食物。",                     # mistakes 食 for noun
    "阿公的腳手猶閣真𠢕。": "爷爷的脚手还真厉害。",            # literal, awkward
    "明仔載欲去揣朋友。": "明天载要去找朋友。",               # mis-parses 明仔載
}

ALL_MINERS: dict[int, dict[str, str]] = {
    0: MINER_0_OUTPUTS,
    1: MINER_1_OUTPUTS,
    2: MINER_2_OUTPUTS,
}
