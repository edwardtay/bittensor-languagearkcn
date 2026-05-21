# LanguageArk-CN — Whitepaper

**Version 0.1 · May 16, 2026**
**Hackathon target:** Proof of Intelligence (Shanghai, May 23, 2026)

---

## 1. Problem

130+ Chinese-language families and minority languages have no commercial ML support: no ASR, no TTS, no machine translation. They die at the rate of one generation per language.

Existing AI labs (OpenAI, Anthropic, Google) **structurally cannot solve this** — these languages have no commercial training data, no large supervised dataset, and no centralized buyer. Bittensor's incentive layer is uniquely suited because:

1. Native speakers exist globally but aren't paid to contribute
2. Multiple miners can train competing models with no central authority
3. The ground truth (does the model work for a native speaker?) is decentralized
4. Yuma Consensus naturally bonds validators to miners that improve the asset

## 2. Why Hokkien for v1

| Property | Implication |
|---|---|
| Meta chose Hokkien for SeamlessM4T (Oct 2022) | Strongest "hardest case" narrative |
| No standardized written form | ASR cannot cheat via text lookup |
| 50M speakers across Fujian, Taiwan, Singapore, Malaysia | Real diaspora buyer base |
| Open baseline exists (Meta HK↔EN S2ST) | Forkable, improvable starting point |
| Common Voice `nan-tw` corpus exists | Validation data available day-1 |

## 3. Mechanism design

### 3.1 Actors

```
                       ┌─────────────────────────┐
                       │ Native-speaker DAO      │
                       │ (per language)          │
                       │ stake-bonded; 2-of-3    │
                       │ attestation for speakers│
                       └────────┬────────────────┘
                                │ pairwise Elo
                                ▼
   ┌──────────┐  Synapse   ┌──────────┐  GLM-4.6   ┌──────────┐
   │  Miners  │ ─────────▶ │ Validators│ ─────────▶│  Yuma    │
   │ (ASR/TTS/│ audio+text │           │ BLEU+FLORES│ Consensus│
   │   MT)    │            │  composite│           │ 41/41/18 │
   └──────────┘            │ score 0-1 │           └──────────┘
                            └──────────┘
```

### 3.2 The composite score

For each miner `m` over an evaluation window:

```
score(m) = w_elo · Elo_norm(m)
        + w_bleu · BLEU_bt(m)
        + w_flores · FLORES200(m)
```

with default weights `w_elo = 0.4`, `w_bleu = 0.3`, `w_flores = 0.3` (governance-tunable).

#### 3.2.1 Elo signal

Pairwise comparisons by registered native speakers. A speaker is shown two candidate outputs (e.g. two ASR transcripts of the same Hokkien audio) and votes. Updated via **Glicko-2** (handles uncertainty + inactivity decay).

Normalization to `[0, 1]`:

```
Elo_norm(m) = sigmoid((rating(m) - 1500) / 400)
```

#### 3.2.2 Back-translation BLEU (the GLM-4.6 signal)

For translation/transcription tasks:

```
text_hokkien --[miner]--> text_mandarin
text_mandarin --[GLM-4.6]--> text_hokkien_round_trip
BLEU_bt = sacreBLEU(text_hokkien, text_hokkien_round_trip)
```

GLM-4.6 chosen because:
- Sponsor (Zhipu) is in the judging room
- Outperforms GPT-4 on Chinese-language benchmarks (C-Eval, CMMLU)
- Free credits via sponsor allocation
- Domestic API (no GFW risk during Shanghai demo)

#### 3.2.3 FLORES-200 held-out

Public sentence-level test set; rotated weekly to prevent overfitting. Hokkien (nan) is a covered FLORES language.

### 3.3 Validator weight vector

Every tempo, each validator submits a weight vector `W_i` where `W_ij = score(miner j)`. Validators MUST commit-reveal (see §4.1).

### 3.4 Yuma processing (chain side)

Standard Yuma Consensus v3 (no fork). The subnet leverages:

- Stake-weighted median consensus C_j to clip outliers
- κ-clipping at `kappa = 0.6` (above default 0.5)
- Bonds EMA at `bonds_moving_avg = 900_000`
- 41% miner / 41% validator+stakers / 18% subnet-owner split

## 4. Anti-gaming defenses

### 4.1 Weight copying — Commit-reveal

Without defense: anyone reads on-chain weights and copies the consensus, harvesting vTrust for free.

**Defense:** `commit_reveal_period = 5 tempos` (~6 hours). Validators submit `hash(weights || nonce)` now; reveal `(weights, nonce)` 5 tempos later. Late reveals are slashed.

```
At tempo t:    submit H = sha256(W_t || nonce_t)
At tempo t+5:  reveal (W_t, nonce_t); chain verifies H
```

### 4.2 Validator cabal — κ-clipping

Default Yuma already clips at κ ≈ 0.5. We raise to `kappa = 0.6`, requiring >60% stake to move consensus on any miner.

### 4.3 Sybil speakers — DAO 2-of-3 attestation

A registered native speaker must:

1. Stake `100 TAO` (slashable)
2. Be attested by 2 of 3 active speaker-validators for that language
3. Lose stake on retraction (e.g. if downstream Elo votes consistently disagree with FLORES + BLEU signals)

The DAO is per-language, bootstrapped via grant: Hokkien speakers in Singapore/Penang/Manila/Fujian community orgs.

### 4.4 Sybil miners — burn cost + immunity + deregistration

Standard Bittensor: dynamic burn cost (~3000+ TAO at network level), `immunity_period = 5000 blocks`, lowest-incentive miners deregistered each interval.

### 4.5 Model copying — proof of training

Miners commit `sha256(loss_curve || dataset_hash || final_weights_hash)` before serving on chain. A copied model has a discontinuous loss curve when audited.

### 4.6 Bond whipsaw — tight liquid-α

```
alpha_low  = 0.05   (655 in u16)
alpha_high = 0.35   (22937 in u16)
```

Default Bittensor (`0.1`/`0.8`) is too loose; whales whipsaw α to escape consensus penalty. Tight bounds at 0.05–0.35 give bonds 3–20 epoch memory — enough to penalize misbehavior, slow enough to prevent gaming.

### 4.7 Min-weight spread

```
min_allowed_weights = 16
```

Validators MUST spread weight across at least 16 miners. Single-miner cabal pumps fail.

## 5. Hyperparameter summary (subnet-create call)

```python
sn = bittensor.subtensor().create_subnet(
    netuid=NEW,
    tempo=360,
    immunity_period=5_000,
    activity_cutoff=5_000,
    kappa=0.6,                          # 39320 in u16
    alpha_low=0.05,                     # 3277 in u16
    alpha_high=0.35,                    # 22937 in u16
    bonds_moving_avg=900_000,
    min_allowed_weights=16,
    max_weights_limit=2**16 - 1,
    weights_rate_limit=100,
    commit_reveal_period=5,             # tempos
    min_burn=int(0.0005e9),             # 0.0005 TAO in rao
    max_burn=int(100e9),                # 100 TAO in rao
)
```

## 6. Economics

Per epoch (`tempo = 360` blocks, ~72 min) alpha distribution:

- **41%** → miners, distributed by incentive `I = normalize(W'ᵀ · S)`
- **41%** → validators + their delegators, distributed by dividends `D = normalize(B · I)`
- **18%** → subnet owner (LanguageArk-CN treasury)

### Owner-treasury usage

The 18% owner cut funds:
1. **Speaker-DAO bootstrapping grants** (paying first 100 native speakers per language)
2. **FLORES test-set rotation** (paid corpus curation)
3. **GLM API costs** (until Zhipu credits exhausted)
4. **Compute for held-out evaluation** (validator-side, not gameable)

## 7. Roadmap

| Phase | Deliverable | When |
|---|---|---|
| **v0 (this hackathon)** | Hokkien-only working prototype + whitepaper + slides | May 23 |
| **v0.5** | Speaker-DAO recruited (50 Hokkien speakers across Fujian/Taiwan/SG) | Q3 2026 |
| **v1** | Mainnet subnet registration; Cantonese + Hakka added | Q4 2026 |
| **v2** | Tibetan, Uyghur, Mongolian onboarded with regional DAO partners | 2027 |
| **v3** | API gateway: Mozilla Common Voice + UNESCO + State Language Commission paying for endpoints | 2027 |

## 8. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Native speakers won't show up | Pre-LOI with 3 Hokkien diaspora orgs (Penang, Singapore, San Francisco) |
| Politically sensitive minority languages (Uyghur, Tibetan) | Launch China-mainland-safe languages first (Hokkien, Cantonese, Hakka, Wu); add minority languages via international DAO branches |
| GLM-4.6 API quotas | Multi-provider failover (Qwen, ERNIE, DeepSeek-V3 as fallback) |
| BLEU is gameable | Triple signal (Elo + BLEU + FLORES) means BLEU alone cannot dominate |
| Yuma constants may change | Spec frozen against chain spec ver TBD; auto-upgrade via owner multisig |

## 9. Why we win this ideathon

| Judging axis | Our answer |
|---|---|
| **产品力 (product)** | Six buyer categories with existing budget lines (Mozilla Foundation grants, 14th FYP cultural-heritage line items, UNESCO endangered-language program, iFlytek/Baidu/Ali speech-data procurement, diaspora-app revenue) |
| **组织力 (organization)** | Native-speaker DAOs solve the global-coordination problem; explicit grant-bootstrapping plan |
| **验证力 (verification)** | 3 independent signals — Elo + BLEU + FLORES — automatable in code (this repo) |
| **博弈力 (game-theory)** | Commit-reveal + κ=0.6 + tight α + min-weight-spread + proof-of-training; each defends a known attack with a specific hyperparam |

---

## Appendix A: Pseudocode for the validator scoring loop

```python
def score_miner(miner_uid: int, eval_window: list[EvalSample]) -> float:
    # 1. Elo signal (cached from speaker DAO)
    elo = speaker_dao.elo(miner_uid, lang="nan")
    elo_norm = sigmoid((elo - 1500) / 400)

    # 2. BLEU back-translation signal
    bleu_scores = []
    for sample in eval_window:
        mandarin = query_miner(miner_uid, sample.hokkien_audio)
        back = glm.translate(mandarin, src="zh", tgt="nan")
        bleu_scores.append(sacrebleu.sentence_bleu(sample.hokkien_text, [back]).score / 100)
    bleu = np.mean(bleu_scores)

    # 3. FLORES held-out
    flores = evaluate_on_flores(miner_uid, lang="nan",
                                 seed=current_tempo // 7)  # rotates weekly

    return 0.4 * elo_norm + 0.3 * bleu + 0.3 * flores
```

## Appendix B: References

- [Yuma Consensus v3 docs](https://docs.learnbittensor.org/learn/yuma-consensus)
- [Commit-Reveal pattern](https://docs.learnbittensor.org/concepts/commit-reveal)
- [Meta SeamlessM4T Hokkien announcement (2022)](https://about.fb.com/news/2022/10/hokkien-ai-speech-translation/)
- [FLORES-200 dataset](https://github.com/facebookresearch/flores)
- [Common Voice nan-tw](https://commonvoice.mozilla.org/nan-tw)
- [Glicko-2 system (Glickman)](http://www.glicko.net/glicko/glicko2.pdf)
- [Zhipu GLM-4.6 API](https://open.bigmodel.cn/dev/api)
