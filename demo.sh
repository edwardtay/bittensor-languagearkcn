#!/usr/bin/env bash
# 90-second scripted demo for the Shanghai judging floor.
# Each step is timeboxed in comments; the actual script runs in <30s.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

echo
echo "════════════════════════════════════════════════════════════════"
echo " LanguageArk-CN — Hokkien (Min Nan) demo"
echo " Proof of Intelligence ideathon, Shanghai · May 23 2026"
echo "════════════════════════════════════════════════════════════════"
echo

# ── 0-10s: pitch (verbal; we just print the framing)
echo "❶  问题: 中国 130+ 种濒危方言, 零条 Bittensor 子网解决"
echo "    Problem: 130+ endangered Chinese-language families. No Bittensor subnet addresses them."
echo
sleep 1

# ── 10-25s: register speakers (the 组织力 part)
echo "❷  Bootstrap native-speaker DAO (Hokkien, 2-of-3 attestation, 100 TAO stake each)"
python -m languageark.cli_bootstrap || true
echo

# ── 25-45s: run 3 mock miners with varying quality
echo "❸  Run 3 miners (uid 0, 1, 2) — they each produce Hokkien→Mandarin translations"
python -m languageark.miner --uid=0 --lang=nan --mode=mock
python -m languageark.miner --uid=1 --lang=nan --mode=mock
python -m languageark.miner --uid=2 --lang=nan --mode=mock
echo

# ── 45-70s: validator scores all three with the 3-signal composite
echo "❹  Validator runs 3-signal composite score (Elo + GLM-4.6 BLEU + FLORES)"
python -m languageark.validator --netuid=999 --lang=nan
echo

# ── 70-85s: commit-reveal explanation already printed by validator

# ── 85-90s: buyer slide (printed)
cat <<'EOF'
❺  Buyers (产品力):
      • Mozilla Common Voice   — dataset payouts
      • 国家语言文字工作委员会   — 数字化方言 budget line
      • UNESCO                 — endangered-language grants
      • Baidu / Alibaba / iFlytek — training-data procurement
      • Diaspora apps (HiNative / Drops / Tandem)
EOF
echo
echo "  ✔ end of 90s pitch — questions?"
