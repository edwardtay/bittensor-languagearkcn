# CLAUDE.md — LanguageArk-CN

> Steering doc. Read this first every session. Update as decisions are made.

## What this is

A **Bittensor subnet** that turns endangered-Chinese-language preservation (Hokkien / Min Nan, Cantonese, Hakka, Wu, Xiang, Uyghur, Tibetan, Mongolian, Zhuang, Yi, etc.) into a verifiable, anti-gaming, buyer-backed intelligence commodity market.

Built for the **Proof of Intelligence: AI Subnet 创意黑客松** in Shanghai, May 23, 2026. Organized by HackQuest + The Mu. Sponsored by **Zhipu (GLM API credits)** and **Alibaba Cloud (compute credits)**. Top-5 advance to **Bittensor China Hacker House**.

## The judging rubric (memorize)

This is an **ideathon, not a code-sprint**. Judges weight **mechanism design over coding**. Four axes:

1. **产品力 (product strength)** — what digital intelligence commodity do you propose?
2. **组织力 (organizational capability)** — can you incentivize global contributors?
3. **验证力 (verification capability)** — can you automate auditing via code?
4. **博弈力 (game-theory)** — fraud / Sybil / collusion resistance

Every design choice in this repo must trace to one of these four.

## The pitch in one paragraph (Mandarin + English)

> 中国有 130+ 种濒危方言和少数民族语言。没有一条 Bittensor 子网解决这个问题。我们用 Yuma Consensus 的 commit-reveal + 母语者 DAO,把"语言保护"变成一个可验证、抗作弊、有买家的智能商品市场。

*China has 130+ endangered dialects and minority languages. Zero Bittensor subnets address this. We use Yuma commit-reveal + native-speaker DAOs to turn language preservation into a verifiable, anti-gaming, buyer-backed intelligence commodity market.*

## Buyer side (产品力)

| Buyer | What they pay for | TAM signal |
|---|---|---|
| **Mozilla Common Voice** | Validated dataset contributions | Already a $-funded program |
| **国家语言文字工作委员会 (State Language Commission)** | 数字化方言 (dialect digitization) policy budget | 2026 5-year plan line item |
| **UNESCO** | Endangered-language preservation grants | Multi-million-dollar program |
| **Baidu / Alibaba / iFlytek (科大讯飞) speech teams** | Training data for Chinese-language ASR/TTS | Internal ML budgets |
| **Ethnology departments** (Minzu University, SOAS) | Field-research corpora | Academic grants |
| **Diaspora apps** (HiNative, Tandem, Drops) | Conversation models for heritage learners | Direct revenue |

## Mechanism design (the part judges score)

| Pipeline element | Choice | Anti-gaming reason |
|---|---|---|
| **Miners produce** | ASR / TTS / translation models per language pair (Hokkien↔Mandarin, Hakka↔English, Tibetan↔Mandarin, etc.) | Diverse outputs, no single optimum to copy |
| **Validators score via** | (a) **Pairwise Elo** from native-speaker DAO per language (stake-bonded speakers); (b) **back-translation BLEU** using **GLM-4.6** as cross-checker; (c) **held-out FLORES-200 + minority-lang test set** rotated weekly | 3 independent signals → collusion needs to corrupt all three |
| **Anti weight-copy** | `commit_reveal_period = 5 tempos` (≈6h) | Defeats SN1/SN3-class weight-copy attacks |
| **Anti Sybil-speaker** | Speaker registration requires staked TAO + 2-of-3 native-speaker DAO attestation; `min_allowed_weights = 16` | Forces broad weight distribution, kills cabal payouts |
| **Anti validator cabal** | `kappa = 0.6` (above default 0.5) for κ-clipping | Needs >60% stake to move consensus |
| **Anti model-theft** | On-chain proof-of-training: miners commit `(loss_curve_hash, dataset_hash)` before serving | Detects SN3-class model copying |
| **Liquid-α bounds** | `alpha_low = 0.05 / alpha_high = 0.35` | Tight bounds prevent bond whipsaw |
| **Tempo** | 360 blocks (default) | No reason to deviate |

## Architecture (3 actors)

```
                ┌──────────────────┐
                │  Native-speaker  │  stake-bonded; per-language DAO
                │   DAO (per lang) │  signs off on speaker registration
                └────────┬─────────┘
                         │ pairwise Elo votes
                         ▼
┌─────────┐  Synapse:   ┌────────────┐  GLM-4.6 back-trans BLEU  ┌──────┐
│ Miners  │ ─────────▶  │ Validators │ ──────────────────────▶  │ Chain │
│ (ASR/   │  audio +    │            │   FLORES-200 hidden set   │ Yuma  │
│ TTS/MT) │  text       │ score(m) = │                            │ + bonds│
└─────────┘             │  0.4·Elo + │                            └───────┘
                         │  0.3·BLEU +│
                         │  0.3·FLORES│
                         └────────────┘
```

## Languages we target (v1)

Priority order — start narrow, demo Hokkien only.

1. **Hokkien (闽南语 / Min Nan / 福建话, ISO `nan`)** — v1 demo target. ~50M speakers (Fujian + Taiwan + SG/MY/PH/ID diaspora). Severely under-resourced. **Meta explicitly chose Hokkien for their SeamlessM4T S2ST research (Oct 2022)** because no written tradition + no ASR baseline = hardest mainstream language pair. Perfect demo case.
2. **Cantonese (粤语 / Yue)** — ~80M speakers, no Apple Siri/Alexa support
3. **Hakka (客家话)** — diaspora preservation case
4. **Tibetan (བོད་སྐད་)** — minority + government priority
5. **Uyghur (ئۇيغۇرچە)** — minority + diaspora
6. **Wu (吴语 / Shanghainese)** — major dialect, low ML coverage

## Why GLM-4.6 (and not OpenAI/Claude)

- Sponsor (Zhipu) judges will be in the room
- GLM-4.6 outperforms GPT-4 on Chinese tasks (C-Eval, CMMLU benchmarks)
- Free credits from sponsor
- Domestic API = no GFW issues for Shanghai demo

Use `glm-4.6` model via `https://open.bigmodel.cn/api/paas/v4/chat/completions`.

## Why Alibaba Cloud

- Sponsor compute credits
- PAI (Platform for AI) has built-in ASR (Whisper variants tuned for Chinese)
- DataWorks for pulling Common Voice / public corpora
- ECS GPU instances (V100, A100, H100 spot)

## Repo layout (target)

```
.
├── CLAUDE.md            ← this file
├── README.md            ← public pitch (one page)
├── whitepaper.md        ← full mechanism design
├── pyproject.toml       ← uv/poetry config
├── languageark/
│   ├── bt_protocol.py   ← real bt.Synapse types (HokkienASR / MT / TTS)
│   ├── miner.py         ← reference miner (Whisper-small Hokkien)
│   ├── validator.py     ← scoring pipeline w/ GLM + FLORES + Elo
│   ├── scoring.py       ← the composite score function
│   ├── glm_client.py    ← Zhipu API wrapper
│   ├── elo.py           ← Glicko-2 implementation
│   └── speaker_dao.py   ← on-chain speaker registry shim
├── tests/
│   ├── test_scoring.py
│   ├── test_glm_client.py
│   └── test_bt_protocol.py
├── docker-compose.yml   ← local subtensor + miner + validator
├── demo.sh              ← 90s scripted demo
└── slides/
    └── pitch.md         ← marp / reveal.js source
```

## Demo plan (90 seconds, judging-floor)

1. **0-10s** — Title slide. State problem in 中文. "130+ 种濒危方言, 零条子网."
2. **10-25s** — Architecture diagram. 3 actors. Anti-gaming pipeline.
3. **25-45s** — Live: run `python -m languageark.miner --lang=nan` (Hokkien Whisper-small). Show it answer a Hokkien audio clip.
4. **45-70s** — Live: run `python -m languageark.validator`. Show score breakdown: Elo 0.72 + BLEU 0.81 + FLORES 0.68 → composite 0.74. Print as JSON. Highlight GLM-4.6 API call in stdout.
5. **70-85s** — Show `commit_reveal` flow on chain (mock txn). Explain weight-copy defense in 5 seconds.
6. **85-90s** — Buyer slide. "Mozilla, 国家语委, UNESCO." Total addressable: $XXM.

## Build phases (priority order, time-boxed)

### Phase 1 — Pitch & whitepaper (do first, this is what wins)
- [ ] `README.md` — one-page public pitch
- [ ] `whitepaper.md` — full mechanism with formulas
- [ ] `slides/pitch.md` — 8-slide deck

### Phase 2 — Working prototype (Hokkien only)
- [ ] `bt_protocol.py` — bt.Synapse types
- [ ] `scoring.py` — composite score function (deterministic, unit-tested)
- [ ] `glm_client.py` — Zhipu GLM-4.6 API wrapper
- [ ] `elo.py` — Glicko-2
- [ ] `miner.py` — minimal Whisper-small wrapper
- [ ] `validator.py` — full scoring pipeline
- [ ] `tests/` — at least scoring + GLM stub tests

### Phase 3 — Polish
- [ ] `docker-compose.yml` — one-command local demo
- [ ] `demo.sh` — recorded fallback in case live fails
- [ ] CLI: `python -m languageark.miner --lang=nan`

### Phase 4 — Stretch
- [ ] Speaker DAO shim (just a JSON file + a "register speaker" CLI)
- [ ] On-chain commit-reveal mock (no real chain — fake hashes printed)
- [ ] Hakka second-language demo

## Non-goals (resist scope creep)

- ❌ Running a real subtensor local node — judges don't have time
- ❌ Real bittensor SDK wiring — mock the chain; show the *mechanism*
- ❌ Training a model from scratch — fork Whisper-small
- ❌ Multi-language v1 — Hokkien only for demo
- ❌ Real on-chain commit-reveal — print mock hashes
- ❌ Building a fancy UI — judges read terminal output

## What "near-completion" looks like

- ✅ Whitepaper that traces every design choice to 4 judging axes
- ✅ README pitch that an investor could read in 90s
- ✅ Prototype that runs `python -m languageark.validator --miner-uid=0` and prints a real score using GLM-4.6
- ✅ Slides (8 frames) usable as-is
- ✅ Demo script that survives a network outage (pre-recorded fallback)

## Sources & reference repos

- Bittensor subnet template: https://github.com/latent-to/bittensor-subnet-template
- SN1 Apex (prompting reference): https://github.com/macrocosm-os/apex
- SN37 finetuning (tournament pattern): https://github.com/macrocosm-os/finetuning
- Yuma consensus docs: https://docs.learnbittensor.org/learn/yuma-consensus
- Commit-reveal: https://docs.learnbittensor.org/concepts/commit-reveal
- Zhipu API docs: https://open.bigmodel.cn/dev/api
- Mozilla Common Voice (Min Nan / Taiwanese Hokkien): https://commonvoice.mozilla.org/nan-tw
- FLORES-200 (includes Min Nan): https://github.com/facebookresearch/flores
- Whisper Hokkien fine-tunes on HF: https://huggingface.co/models?search=whisper+hokkien
- **Meta SeamlessM4T Hokkien S2ST** (canonical low-resource Hokkien research, Oct 2022): https://about.fb.com/news/2022/10/hokkien-ai-speech-translation/
- Meta `hokkien_translation` repo: https://github.com/facebookresearch/fairseq/tree/ust/examples/hokkien
- The intel report this came from: `/home/edwardtay/2-projects/bittensor/README.md` (sections: Ideathon, Builder Advanced)

## Current status (updated 2026-05-21, v3)

Submission-ready. Docs: README, whitepaper, partners, OPS, HONESTY. Code: 57 pytest + 8 forge = **65/65 passing**. Live finney-readable chain probe, real FLORES-200 (997 yue↔zho pairs), real chrF++/WER, Glicko-2, Yuma attack sim, on-chain SpeakerDAO (Foundry), Claude + GLM judges. Static site builds from artifacts (`scripts/build_site.py`); custom favicon/logo (`site/favicon.svg`); docker-compose for offline demo.

Stretch / event-day only:

1. `export ZHIPU_API_KEY=…` from sponsor booth → re-run `demo.sh` to swap Claude judge for GLM-4.6.
2. `python -m languageark.seamless_miner` on a GPU box → real Hokkien translations (9.5 GB VRAM).
3. `npx @marp-team/marp-cli slides/pitch.md --pdf` for projector.
4. `asciinema rec` the demo as network-outage fallback.

## Decisions log

- **2026-05-16** — Project started. Single language for demo: **Hokkien / Min Nan (ISO `nan`)**. Rationale:
  - Meta themselves chose Hokkien as their canonical low-resource case (SeamlessM4T 2022) → strong narrative
  - No standardized written form → harder problem → bigger differentiation
  - 50M speakers across Fujian, Taiwan, SG, MY, PH, ID — diaspora story for Shanghai judges
  - Common Voice `nan-tw` corpus exists with hours of validated audio
  - Meta released open Hokkien S2ST + HK→EN/EN→HK checkpoints (free baseline to beat)
- **2026-05-16** — Use GLM-4.6 not GPT/Claude. Sponsor optics + better Chinese.
- **2026-05-16** — No real subtensor node in demo. Mock the chain layer. Mechanism is the product.
