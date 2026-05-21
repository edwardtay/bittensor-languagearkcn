# LanguageArk-CN

> **Endangered-Chinese-language preservation, priced and verified on Bittensor.**
> v1 demo: Hokkien / Min Nan (ISO `nan`) — Meta's canonical low-resource language.

Built for **Proof of Intelligence: AI Subnet 创意黑客松** · Shanghai · 2026-05-23.
Sponsors: Zhipu (GLM-4.6) · Alibaba Cloud.

🌐 **Live:** https://language-ark-cn.lever-labs.com
📊 **Tests:** 57 pytest + 8 forge = **65/65 passing** · **2.3s** end-to-end demo · zero API keys required

### Judge's quickstart (≤ 5 minutes)

| Want to see… | Open / run |
|---|---|
| 🎯 The pitch in 13 slides | [`site/slides.html`](https://language-ark-cn.lever-labs.com/slides.html) |
| 📜 Mechanism design (9 sections) | [`whitepaper.md`](whitepaper.md) · [`/whitepaper/`](https://language-ark-cn.lever-labs.com/whitepaper/) |
| 🔬 What's real vs. toy | [`HONESTY.md`](HONESTY.md) |
| 🛠 How it would actually operate | [`OPS.md`](OPS.md) — runbooks, cost model, incidents |
| 🤝 Diaspora partner orgs | [`partners.md`](partners.md) |
| 🧪 Run the demo locally | `bash demo.sh` (2.3 s, no keys) |
| ⚔️ The attack-defense proof | `python -m languageark.attack` (100 % vs 42 % knockout) |
| ⛓ Solidity Speaker DAO | `cd contracts && forge test` (8 passing) |

```bash
git clone https://github.com/edwardtay/bittensor-languagearkcn
cd bittensor-languagearkcn && python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
bash demo.sh        # 7-step Hokkien scoring + Yuma attack sim
pytest -q           # 57 passed
```

---

## Problem · Mechanism · Proof

**Problem.** 130+ endangered Chinese-language + minority families. No commercial ASR/TTS/MT. Zero of 128 Bittensor subnets address it.

**Mechanism.** 3-signal composite score, each signal independent — collusion needs to corrupt all three:

```
score = 0.4·Elo(speaker-DAO, Glicko-2) + 0.3·BLEU_bt(GLM-4.6 / Claude) + 0.3·FLORES-200
```

**Proof — live scoring** (from `bash demo.sh`):

```
 uid    Elo  BLEU_bt  FLORES  composite      W
   0   1751   1.000   1.000      0.861   0.485    ← professional
   1   1481   1.000   0.062      0.514   0.290    ← competent
   2   1243   0.875   0.000      0.400   0.226    ← poor
```

**Proof — attack defeated** (`python -m languageark.attack`): weight-copying freeloader earns **100%** of dividends on a vulnerable subnet → **42%** on ours. One hyperparam (`commit_reveal_period = 5`) buys a 58-point swing.

## Anti-gaming defenses

| Attack | Defense | Hyperparam |
|---|---|---|
| Weight copying | Commit-reveal | `commit_reveal_period = 5` |
| Validator cabal | κ-clipping | `kappa = 0.6` |
| Sybil speakers | 2-of-3 DAO attestation + 100 TAO stake | on-chain (`SpeakerDAO.sol`) |
| Single-miner cabal | Min weight spread | `min_allowed_weights = 16` |
| Liquid-α bond whipsaw | Tight α bounds | `alpha_low/high = 0.05 / 0.35` |
| Model copying | Proof-of-training hash | on-chain commit |

Full derivation in [`whitepaper.md`](whitepaper.md) §4.

## Why Hokkien for v1

Meta's canonical low-resource case (SeamlessM4T, 2022). No standardized written form (ASR can't cheat by reading text). 50M speakers — Fujian, Taiwan, SG/MY/PH/ID diaspora. Open baseline exists. Common Voice `nan-tw` ready as day-1 validation.

## Buyers

Mozilla Common Voice · 国家语言文字工作委员会 (数字化方言 budget) · UNESCO grants · Baidu / Alibaba / iFlytek speech-AI data · diaspora apps (HiNative · Drops · Tandem). Concrete partner orgs across 4 hubs (Fujian / Taiwan / SG / Penang) in [`partners.md`](partners.md).

## Repo layout

```
languageark/
  bt_protocol.py     real bt.Synapse types (ASR / MT / TTS, Han + POJ + TLPA)
  chain.py           live finney/test/local metagraph probe
  scoring.py         composite score (0.4·Elo + 0.3·BLEU + 0.3·FLORES)
  glm_client.py      Zhipu GLM-4.6 + Anthropic Claude judge + mock fallback
  elo.py             Glicko-2 (Illinois volatility)
  metrics.py         chrF++ / WER via sacrebleu
  flores_loader.py   997 yue_Hant ↔ zho_Hans FLORES-200 pairs
  eval_samples.py    Hokkien curated pairs + 3-tier miner outputs
  speaker_dao.py     2-of-3 attestation registry (JSON shim)
  miner.py · claude_miner.py · nllb_miner.py · seamless_miner.py
  validator.py       end-to-end scoring pipeline (mock + on-chain modes)
  attack.py          Yuma weight-copy simulator (100% vs 42% knockout)
  subnet_register.py btcli mainnet command sheet
contracts/           Foundry: SpeakerDAO.sol (stake + attest + slash + rating)
scripts/             build_site.py, deploy_speaker_dao_local.py, validator_e2e_onchain.py
tests/               57 pytest + 8 forge = 65 passing
slides/pitch.md      13-slide marp deck
whitepaper.md · partners.md · OPS.md · HONESTY.md
demo.sh              7-step demo, ~2.3s wall-clock, no API key required
docker-compose.yml   site + (stub) subtensor + miner + validator
```

## Roadmap

| Phase | Deliverable | When |
|---|---|---|
| **v0** (this hackathon) | Hokkien prototype + whitepaper + slides + attack sim | May 23 2026 |
| **v0.5** | 50 Hokkien speakers signed across Fujian / Taiwan / SG | Q3 2026 |
| **v1** | Mainnet subnet registered; Cantonese + Hakka added | Q4 2026 |
| **v2** | Tibetan / Uyghur / Mongolian via regional DAO branches | 2027 |
| **v3** | API revenue from Mozilla / UNESCO / 国家语委 | 2027 |

## Demo notes

`bash demo.sh` runs in **~2.3s** with no API keys. The `bittensor` SDK (v10.3.2) is imported (`bt.Synapse` subclasses real, `chain.py` reads live finney when networked). No chain node, no GPU. Judge tier auto-selects: `ANTHROPIC_API_KEY` → Claude · `ZHIPU_API_KEY` → GLM-4.6 · neither → heuristic mock. At the event, `export ZHIPU_API_KEY=…` to swap to GLM (sponsor optics).

MIT licensed.
