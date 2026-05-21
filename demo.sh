#!/usr/bin/env bash
# 90-second scripted demo for the Shanghai judging floor.
# Runs end-to-end with or without ZHIPU_API_KEY (mock-GLM fallback).
set -eu
# Note: NOT pipefail — we `| head` several outputs and don't want SIGPIPE to exit.

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

if [[ -d .venv ]]; then
    export PATH="$ROOT/.venv/bin:$PATH"
fi

echo
echo "════════════════════════════════════════════════════════════════"
echo " LanguageArk-CN — Hokkien (Min Nan) demo"
echo " Proof of Intelligence ideathon, Shanghai · May 23 2026"
echo "════════════════════════════════════════════════════════════════"
echo

# ── ❶ Problem framing
echo "❶  问题: 中国 130+ 种濒危方言, 零条 Bittensor 子网"
echo "    Even FLORES-200 (Meta's 200-language benchmark) has NO Hokkien."
echo "    That gap is exactly the market this subnet fills."
echo

# ── ❷ Real bittensor SDK + Synapse types
echo "❷  REAL bittensor SDK integration (not pydantic stubs)"
python -m languageark.chain synapse-demo 2>&1 | head -12
echo

# ── ❸ Speaker DAO bootstrap
echo "❸  Bootstrap native-speaker DAO (2-of-3 attestation, 100 TAO stake)"
rm -f data/speaker_dao.json
python -m languageark.cli_bootstrap
echo

# ── ❹ Score on curated Hokkien set
echo "❹  Score 3 miners on curated Hokkien eval set (10 pairs)"
python -m languageark.validator --eval-set hokkien
echo

# ── ❺ Score on REAL FLORES-200 yue↔zho (997 pro-translated sentences)
echo "❺  Score on REAL FLORES-200 yue_Hant↔zho_Hans (Cantonese family proxy)"
python -m languageark.validator --eval-set flores-yue
echo

# ── ❻ Attack simulator
echo "❻  博弈力: weight-copy attack vs commit-reveal defense"
python -m languageark.attack 2>&1 | tail -20
echo

# ── ❼ Mainnet registration command sheet
echo "❼  Mainnet registration command sheet (we know the chain interface)"
python -m languageark.subnet_register --wallet=languageark --hotkey=owner --network=finney 2>&1 | head -25
echo "   [... full sheet via: python -m languageark.subnet_register ...]"
echo

# ── ❽ Buyer slide
cat <<'EOF'
❽  Buyers (产品力):
      • Mozilla Common Voice           — pays for validated dataset contributions
      • 国家语言文字工作委员会          — 数字化方言 budget line
      • UNESCO                         — endangered-language preservation grants
      • iFlytek / Baidu / Alibaba      — speech-AI training data procurement
      • Diaspora apps                  — HiNative, Drops, Tandem
EOF
echo
echo "  ✔ end of demo — 谢谢"
