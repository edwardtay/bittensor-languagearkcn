#!/usr/bin/env bash
# 90-second scripted demo for the Shanghai judging floor.
# Runs end-to-end with or without ZHIPU_API_KEY (mock-GLM fallback).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

# Use venv if present
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
echo "❶  问题: 中国 130+ 种濒危方言, 零条 Bittensor 子网解决"
echo "    Problem: 130+ endangered Chinese languages. No Bittensor subnet addresses them."
echo "    v1 demo: Hokkien (Min Nan, ISO nan) — Meta's canonical low-resource case."
echo

# ── ❷ Bootstrap speaker DAO
rm -f data/speaker_dao.json data/mock_miners.json 2>/dev/null || true
echo "❷  Bootstrap native-speaker DAO (2-of-3 attestation, 100 TAO stake)"
python -m languageark.cli_bootstrap
echo

# ── ❸ Three miners of varying quality
echo "❸  Run 3 miners (uid 0=professional, 1=competent, 2=poor)"
python -m languageark.miner --uid=0 --lang=nan --mode=mock
python -m languageark.miner --uid=1 --lang=nan --mode=mock
python -m languageark.miner --uid=2 --lang=nan --mode=mock
echo

# ── ❹ Validator scoring with 3-signal composite
echo "❹  Validator: 3-signal composite = 0.4·Elo + 0.3·BLEU_bt + 0.3·FLORES"
python -m languageark.validator --netuid=999 --lang=nan
echo

# ── ❺ Attack demo — the 博弈力 moment
echo "❺  博弈力 demo: weight-copy attack vs commit-reveal defense"
python -m languageark.attack
echo

# ── ❻ Mainnet registration command sheet
echo "❻  Mainnet registration (we know the chain interface)"
python -m languageark.subnet_register --wallet=languageark --hotkey=owner --network=finney
echo

# ── ❼ Buyer slide (verbal)
cat <<'EOF'
❼  Buyers (产品力):
      • Mozilla Common Voice           — pays for validated dataset contributions
      • 国家语言文字工作委员会          — 数字化方言 budget line
      • UNESCO                         — endangered-language preservation grants
      • iFlytek / Baidu / Alibaba      — speech-AI training data procurement
      • Diaspora apps                  — HiNative, Drops, Tandem
EOF
echo
echo "  ✔ end of demo — 谢谢"
