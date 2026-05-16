---
marp: true
theme: default
size: 16:9
paginate: true
---

# LanguageArk-CN
### 中文濒危语言保护子网

Proof of Intelligence Shanghai · May 23, 2026

---

## 问题 / The Problem

- China has **130+ endangered dialects + minority languages**
- Hokkien, Cantonese, Hakka, Wu, Tibetan, Uyghur, Mongolian, Zhuang, Yi…
- **No commercial ASR / TTS / MT** — Siri/Alexa/Bixby skip them
- **Zero of the 128 Bittensor subnets address this**

---

## v1 demo: **Hokkien (Min Nan, ISO `nan`)**

- 50M speakers · Fujian + Taiwan + SG/MY/PH/ID diaspora
- **Meta themselves** chose it as their canonical low-resource case (SeamlessM4T 2022)
- **No standardized writing system** → ASR can't cheat by reading text
- Open baseline exists — forkable, improvable starting point

---

## Mechanism (the 验证力 part)

```
score(miner) = 0.4 · Elo (native-speaker DAO)
             + 0.3 · BLEU (back-translation via Zhipu GLM-4.6)
             + 0.3 · FLORES-200 (held-out, rotated weekly)
```

**3 independent signals** — collusion must corrupt all three.

---

## Anti-gaming (the 博弈力 part)

| Attack | Defense | Hyperparam |
|---|---|---|
| Weight copying | Commit-reveal | `commit_reveal_period = 5` |
| Validator cabal | κ-clipping | `kappa = 0.6` |
| Sybil speakers | DAO 2-of-3 attest + 100 TAO stake | off-chain |
| Single-miner cabal | min weight spread | `min_allowed_weights = 16` |
| Liquid-α bond whipsaw | tight α bounds | `0.05 / 0.35` |
| Model copying | proof-of-training hash | on-chain commit |

---

## Architecture (3 actors)

```
   Miners            Validators            Native-speaker DAO
   (ASR/TTS/MT)  →   (composite score)  ←  (per-language, stake-bonded)
                       ↓
                    Yuma Consensus (41/41/18)
```

---

## Buyers (产品力)

- **Mozilla Common Voice** — pays for validated datasets
- **国家语言文字工作委员会** — 数字化方言 policy budget
- **UNESCO** — endangered-language preservation grants
- **Baidu / Alibaba / iFlytek 科大讯飞** — speech-AI training data
- **Diaspora apps** — HiNative, Drops, Tandem

---

## Why this wins this ideathon

| Axis | Our answer |
|---|---|
| **产品力** | Concrete buyers w/ budget lines; underserved market |
| **组织力** | Per-language speaker DAOs solve global coordination |
| **验证力** | 3 independent signals automatable in <500 LoC |
| **博弈力** | Commit-reveal + κ=0.6 + tight α + min-spread + PoT |

---

## Live demo

```bash
$ ./demo.sh

❶  Problem: 130+ endangered languages, 0 subnets
❷  Bootstrap Hokkien speaker DAO (3 speakers, 100 TAO each)
❸  Run 3 mock miners
❹  Validator: Elo + GLM-4.6 BLEU + FLORES = composite score
❺  commit_reveal hash printed (anti-weight-copy)
```

---

## Roadmap

- **v0** — this hackathon: Hokkien prototype + whitepaper
- **v0.5** — Q3 '26: 50 Hokkien speakers across Fujian/TW/SG
- **v1** — Q4 '26: mainnet subnet; Cantonese + Hakka added
- **v2** — 2027: Tibetan/Uyghur/Mongolian via regional DAOs
- **v3** — 2027: API revenue from Mozilla, 国家语委, UNESCO

---

# Thank you · 谢谢 · Multo salamat · Terima kasih

`github.com/edwardtay/bittensor-languagearkcn`
