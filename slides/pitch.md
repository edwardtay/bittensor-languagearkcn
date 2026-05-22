---
marp: true
theme: default
size: 16:9
paginate: true
header: 'LanguageArk-CN · Proof of Intelligence · Shanghai 2026'
footer: 'github.com/edwardtay/bittensor-languagearkcn'
---

# LanguageArk-CN
## 中文濒危语言保护子网

**Proof of Intelligence ideathon · Shanghai · May 23 2026**
*Team: edward.tay@*

---

## 问题 / The Problem

- China has **130+ endangered Chinese-language families + minority languages**
- Hokkien · Cantonese · Hakka · Wu · Tibetan · Uyghur · Mongolian · Zhuang · Yi…
- **No commercial ASR / TTS / MT** — Siri / Alexa / Bixby skip them all
- Each generation, more disappear

> **Zero of the 128 Bittensor subnets address this.**

---

## v1 demo: Hokkien (Min Nan, ISO `nan`)

| Why this language | Detail |
|---|---|
| **Meta picked it first** | SeamlessM4T S2ST 2022 → canonical low-resource case |
| **No standard written form** | ASR cannot cheat via text lookup |
| **50M speakers** | Fujian + Taiwan + SG/MY/PH/ID — real diaspora buyer base |
| **Open baseline exists** | Meta HK↔EN checkpoint — forkable starting point |
| **Common Voice `nan-tw` corpus** | Day-1 validation data |

---

## Mechanism (验证力)

A **three-signal composite** — collusion needs to corrupt all three.

```
score(miner) = 0.4 · Elo_norm               (native-speaker DAO)
             + 0.3 · BLEU_back_translation  (Zhipu GLM-4.6 as oracle)
             + 0.3 · FLORES-200             (held-out, rotated weekly)
```

Each signal is **independent** and **auditable in code** (this repo, <500 LoC).

---

## Live scoring (real output from this repo)

```
📊 Score breakdown:

 uid    Elo   EloN  BLEU_bt  FLORES  composite      W
   0   1751   0.65   1.000   1.000      0.861   0.485    ← professional
   1   1481   0.49   1.000   0.062      0.514   0.290    ← competent
   2   1243   0.34   0.875   0.000      0.400   0.226    ← poor

🔐 commit_reveal hash submitted now, reveals in 5 tempos
   0xb3adc71597abd9ae03843ebbf9806d74…
```

3 miners. 3 quality tiers. 3 signals correctly differentiate.

---

## Anti-gaming (博弈力)

| Attack | Defense | Hyperparam |
|---|---|---|
| **Weight copying** | Commit-reveal | `commit_reveal_period = 5` |
| Validator cabal | κ-clipping | `kappa = 0.6` (above default) |
| Sybil speakers | 2-of-3 DAO attestation + 100 TAO stake | off-chain |
| Single-miner cabal | Min weight spread | `min_allowed_weights = 16` |
| Liquid-α whipsaw | Tight α bounds | `0.05 / 0.35` |
| Model copying | Proof-of-training | hash-commit loss curve |

---

## The 博弈力 knockout: attack simulator (real output)

We ran a **freeloader-validator** against two networks:

```
── Network A (vulnerable, commit_reveal=0) ──
  freeloader earns 100% of honest dividends WITHOUT DOING ANY WORK

── Network B (LanguageArk-CN, commit_reveal=5) ──
  freeloader earns only 42% of honest dividends — attack defeated
```

**58 percentage-point swing** from one hyperparam choice. Run it yourself:
`python -m languageark.attack`

---

## Architecture (组织力)

```
                        Native-speaker DAO
                        (per language; stake-bonded;
                         2-of-3 attestation gate)
                                  │
                                  │ pairwise Elo
                                  ▼
   Miners                Validators                Yuma
   (ASR/TTS/MT)   ───▶   composite score   ───▶   41/41/18
                        Elo + GLM-4.6 BLEU
                        + FLORES-200
```

Per-language DAOs solve the global-coordination problem cleanly.

---

## Buyers (产品力)

| Buyer | What they pay for |
|---|---|
| **Mozilla Common Voice** | Validated dataset contributions |
| **国家语言文字工作委员会** | 数字化方言 policy budget line |
| **UNESCO** | Endangered-language preservation grants |
| **iFlytek / Baidu / Alibaba** | Speech-AI training data procurement |
| **Diaspora apps** (HiNative · Drops · Tandem) | Heritage-learner content |

Partner orgs identified in `partners.md` — 4 hubs (Fujian · Taiwan · Singapore · Penang).

---

## We know the chain interface

```bash
btcli subnet create --network finney --wallet.name languageark
btcli sudo set --param kappa               --value 39320     # 0.6
btcli sudo set --param commit_reveal_period --value 5
btcli sudo set --param alpha_low           --value 3277      # 0.05
btcli sudo set --param alpha_high          --value 22937     # 0.35
btcli sudo set --param min_allowed_weights --value 16
btcli sudo set --param bonds_moving_avg    --value 900000
# ...full sheet in languageark.subnet_register
```

Each hyperparam traces to a specific defended attack.

---

## Demo (90 seconds)

```bash
$ bash demo.sh

❶  Problem (中文 + EN)
❷  Bootstrap speaker DAO (Xiamen + Taiwan + Penang)
❸  3 miners, 3 quality tiers
❹  Validator → composite score → commit-reveal hash
❺  Attack simulator → 100% vs 42% knockout
❻  btcli registration sheet
❼  Buyer list
```

Runs in **2.3 seconds**. No API key required (Claude / GLM judges optional).

---

## Why we win this ideathon

| Axis | Our answer |
|---|---|
| **产品力** | 6 named buyer categories w/ real budget lines (Mozilla · 国家语委 · UNESCO · iFlytek · diaspora apps) |
| **组织力** | Per-language stake-bonded DAOs; on-chain Solidity contract (8 forge tests); 4 partner hubs scoped |
| **验证力** | 3 independent signals; real `bt.Synapse` types; real FLORES-200 (997 pairs); chrF++ via `sacrebleu` |
| **博弈力** | 6 attacks → 6 named defenses → **Yuma simulator proves 100% → 42% knockout** |

Plus: **71/71 tests pass (63 pytest + 8 Foundry) · live deploy · whitepaper-grade docs**.

---

# 谢谢 · Multo salamat · Terima kasih

**LanguageArk-CN** — endangered-Chinese-language preservation, Bittensor-native.

🌐 https://language-ark-cn.lever-labs.com
`github.com/edwardtay/bittensor-languagearkcn` · `bash demo.sh`
