# LanguageArk-CN

> Endangered-Chinese-language preservation as a Bittensor subnet.
> **v1 demo: Hokkien / Min Nan (ISO `nan`)** — Meta's canonical low-resource language.

Built for **Proof of Intelligence: AI Subnet 创意黑客松** (Shanghai · May 23 2026).
Sponsors: Zhipu (GLM-4.6) · Alibaba Cloud.

```bash
git clone https://github.com/edwardtay/bittensor-languagearkcn
cd bittensor-languagearkcn
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
bash demo.sh        # runs in ~5 seconds, no API key needed
pytest -q           # 38/38 pass
```

---

## The problem

China has **130+ endangered Chinese-language families + minority languages** — Hokkien, Cantonese, Hakka, Wu, Tibetan, Uyghur, Mongolian… They have no commercial ASR/TTS/MT. Siri, Alexa, Bixby all skip them. Each generation, more disappear.

**Zero of the 128 Bittensor subnets address this.**

## The mechanism

LanguageArk-CN turns language preservation into a **verifiable, anti-gaming, buyer-backed intelligence commodity market** using a 3-signal composite score:

```
score(miner) = 0.4 · Elo (native-speaker DAO, Glicko-2)
             + 0.3 · BLEU back-translation (via Zhipu GLM-4.6)
             + 0.3 · FLORES-200 held-out (rotated weekly)
```

Each signal is **independent**. Collusion requires corrupting all three.

## Live scoring output (from this repo)

```
📊 Score breakdown:

 uid    Elo   EloN  BLEU_bt  FLORES  composite      W
   0   1751   0.65   1.000   1.000      0.861   0.485    ← professional
   1   1481   0.49   1.000   0.062      0.514   0.290    ← competent
   2   1243   0.34   0.875   0.000      0.400   0.226    ← poor

🔐 commit_reveal hash submitted now, reveals in 5 tempos
   0xb3adc71597abd9ae03843ebbf9806d74…
```

3 miners with deliberately differing quality → all 3 signals discriminate correctly.

## The 博弈力 knockout — attack simulator

`python -m languageark.attack` runs a **weight-copy attack** side-by-side on two networks:

```
── Network A (vulnerable, commit_reveal=0) ──
  freeloader-validator earns 100% of honest dividends WITHOUT DOING ANY WORK

── Network B (LanguageArk-CN, commit_reveal=5) ──
  freeloader earns only 42% of honest dividends — attack defeated
```

A 58-point swing from one hyperparam (`commit_reveal_period = 5`).

## Anti-gaming defenses (six attacks, six named defenses)

| Attack | Defense | Hyperparam |
|---|---|---|
| Weight copying | Commit-reveal | `commit_reveal_period = 5` |
| Validator cabal | κ-clipping | `kappa = 0.6` |
| Sybil speakers | 2-of-3 DAO attestation + 100 TAO stake | (off-chain) |
| Single-miner cabal | Min weight spread | `min_allowed_weights = 16` |
| Liquid-α bond whipsaw | Tight α bounds | `alpha_low/high = 0.05 / 0.35` |
| Model copying | Proof-of-training hash | on-chain commit |

Each defense in `whitepaper.md` §4. Hyperparam sheet in `subnet_register.py`.

## Why Hokkien for v1

- **Meta themselves picked Hokkien** as their canonical low-resource S2ST case (SeamlessM4T, Oct 2022) — strongest "hardest case" narrative
- **No standardized written form** → ASR cannot cheat by reading text
- **50M speakers** across Fujian, Taiwan, Singapore, Malaysia, Philippines, Indonesia → real diaspora buyer base
- **Open baseline exists** (Meta HK↔EN model on HF) — forkable starting point
- **Common Voice `nan-tw` corpus** exists — validation data day-1

## Buyers (产品力)

- **Mozilla Common Voice** — pays for validated dataset contributions
- **国家语言文字工作委员会** — 数字化方言 policy budget
- **UNESCO** — endangered-language preservation grants
- **Baidu / Alibaba / iFlytek** — speech-AI training data
- **Diaspora apps** — HiNative, Drops, Tandem

Concrete partner orgs (4 hubs: Fujian / Taiwan / Singapore / Penang) in [`partners.md`](partners.md).

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
demo.sh              7-step demo, ~5s, no API key required
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

## How to run the full demo

```bash
bash demo.sh
```

The demo runs end-to-end with **zero external dependencies** at runtime:
- No `ZHIPU_API_KEY` needed (mock-GLM heuristic stand-in is included)
- No bittensor SDK / chain node needed
- No GPU needed (mock-miner mode)

With a real `ZHIPU_API_KEY` (`export ZHIPU_API_KEY=sk-...`), the demo lights up the real GLM-4.6 back-translation BLEU — useful for showing sponsor magic on the judging floor.

## License

MIT.
