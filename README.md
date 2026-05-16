# LanguageArk-CN

> Endangered-Chinese-language preservation as a Bittensor subnet.
> v1 demo: **Hokkien / Min Nan (ISO `nan`)** — Meta's canonical low-resource language.

Built for **Proof of Intelligence: AI Subnet 创意黑客松** (Shanghai, May 23, 2026).

## The problem

China has **130+ endangered dialects and minority languages** (Hokkien, Cantonese, Hakka, Wu, Xiang, Tibetan, Uyghur, Mongolian, Zhuang, Yi, …). They have no commercial ASR/TTS, no Siri/Alexa support, and they're disappearing one generation at a time.

**Zero of the 128 Bittensor subnets address this.**

## The mechanism

LanguageArk-CN turns language preservation into a **verifiable, anti-gaming, buyer-backed intelligence commodity market**.

| Actor | What they do | Reward |
|---|---|---|
| **Miners** | Submit ASR / TTS / translation models per language pair (e.g. Hokkien↔Mandarin) | Alpha tokens proportional to incentive `I` |
| **Validators** | Score miners using a 3-signal composite | Alpha tokens proportional to dividends `D` |
| **Native-speaker DAO** | Per-language quorum stake-bonded; sign off on registrations + cast pairwise Elo votes | Share of validator dividends |

### Composite score (the verification layer)

```
score(miner) = 0.4 · Elo_normalized
             + 0.3 · BLEU_back_translation       (via Zhipu GLM-4.6)
             + 0.3 · FLORES_200_held_out         (rotated weekly)
```

Three **independent** signals — gaming requires corrupting all three at once.

### Anti-gaming (the 博弈力 part judges score)

| Attack | Defense | Hyperparam |
|---|---|---|
| Weight copying | Commit-reveal | `commit_reveal_period = 5 tempos` |
| Validator cabal | κ-clipping | `kappa = 0.6` |
| Sybil speakers | DAO 2-of-3 attestation + min stake | (off-chain) |
| Cabal weight inflation | Min weight spread | `min_allowed_weights = 16` |
| Liquid-α bond whipsaw | Tight α bounds | `alpha_low/high = 0.05/0.35` |
| Model copying | Proof-of-training | hash-commit loss curve |

## Buyers (产品力)

- **Mozilla Common Voice** — pays for validated dataset contributions
- **国家语言文字工作委员会** (China State Language Commission) — 数字化方言 policy budget
- **UNESCO** — endangered-language preservation grants
- **Baidu / Alibaba / iFlytek (科大讯飞)** — speech-AI training data
- **Diaspora apps** (HiNative, Drops, Tandem) — heritage learners

## Why Hokkien for v1

- **Meta picked Hokkien** as their canonical low-resource S2ST case (SeamlessM4T, Oct 2022) — strongest "this is the hardest case" narrative
- **No standardized writing system** → ASR can't cheat by reading text
- **50M speakers** across Fujian, Taiwan, Singapore, Malaysia, Philippines, Indonesia → diaspora-funded buyer base
- **Open baseline exists** (Meta's HK→EN model on Hugging Face) — miners can fork and improve

## Quickstart

```bash
# install
uv sync   # or: pip install -e .

# set Zhipu API key (free credits from sponsor)
export ZHIPU_API_KEY=sk-...

# run a miner
python -m languageark.miner --lang=nan --uid=0

# in another shell, run the validator scoring loop
python -m languageark.validator --netuid=999 --miners=0

# unit-tested score:
pytest -v
```

## Repo layout

```
languageark/
  protocol.py       Synapse types (ASRSynapse, BackTranslateSynapse)
  miner.py          Whisper-small Hokkien wrapper
  validator.py      3-signal composite scoring pipeline
  scoring.py        deterministic composite score function (unit-tested)
  glm_client.py     Zhipu GLM-4.6 API wrapper
  elo.py            Glicko-2 implementation for pairwise speaker votes
  speaker_dao.py    on-chain speaker registry shim
tests/              pytest suite
slides/             8-slide pitch deck (marp)
demo.sh             scripted 90-second demo (with fallback)
```

## Status

- [x] CLAUDE.md steering doc
- [x] README pitch
- [ ] whitepaper.md (full mechanism)
- [ ] scoring.py + tests
- [ ] glm_client.py + tests
- [ ] elo.py
- [ ] miner.py (Whisper-small)
- [ ] validator.py end-to-end
- [ ] slides/pitch.md
- [ ] demo.sh

## License

MIT.
