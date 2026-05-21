# What's real and what's still a toy

A submission like this is easy to oversell. This page is the unvarnished status.

## What's REAL ✅

- **bittensor SDK is genuinely installed and used.** `import bittensor as bt` works (v10.3.2). `HokkienASR` / `HokkienMT` / `HokkienTTS` are real `bt.Synapse` subclasses verifiable via `isinstance(s, bt.Synapse)` (see `tests/test_bt_protocol.py`).
- **`languageark.chain` queries the live chain.** `python -m languageark.chain probe --network finney --netuid 1` reads real metagraph state and hyperparameters from finney/test/local.
- **FLORES-200 data is real and downloaded.** 997 professional-translator sentence pairs in `data/flores/yue_Hant.dev` + `zho_Hans.dev`. Fetched from `dl.fbaipublicfiles.com/nllb/flores200_dataset.tar.gz`.
- **chrF++ and WER are real metrics.** From `sacrebleu`, the same package WMT uses.
- **Glicko-2 is a real implementation.** Full Illinois-algorithm volatility update; tested for monotonicity, draws, and inactivity decay.
- **Attack simulator behaves like real Yuma.** Power-law miner weights + drift-aware vTrust computation. 100% (vulnerable) vs 42% (with commit-reveal) is reproducible.
- **57 Python tests + 8 Solidity tests (65 total) all pass.** Speaker DAO contract added 8 forge tests; AnthropicJudge + miner wrappers added pytest cases.

## What's a TOY ⚠️

These are real engineering gaps. A grant-funded continuation would close them.

| Claim | Reality | What it would take to make real |
|---|---|---|
| "Hokkien speech subnet" | Zero real audio in the demo. No Whisper / SeamlessM4T model loaded. | ~2 hours to wire `facebook/seamless-m4t-v2-large` and feed Common Voice nan-tw audio. Limited by ~10 GB model download. |
| "Hokkien validation corpus" | 10 hand-curated sentence pairs from MoE dictionary. FLORES-200 has no Hokkien (we use Cantonese as a proxy). | Long-term: build the corpus *via* the subnet's speaker DAO — that's the v1 product. Short-term: scrape Wikipedia zh-min-nan parallel articles. |
| ~~"Speaker DAO"~~ ✅ **closed 2026-05-16** | Real Solidity contract `contracts/src/SpeakerDAO.sol` (~130 lines): stake + 2-of-3 attestation + slash + on-chain Glicko rating writeback. 8 forge tests pass; e2e deploy + stake + attest + register + vote + setRating verified on local anvil via `scripts/deploy_speaker_dao_local.py`. | Production: swap minStake from native ETH → Subtensor EVM staking precompile `0x…0805`. |
| "Commit-reveal" | The validator prints a SHA-256 hash; we don't actually wait 5 tempos. | The bittensor SDK has `subtensor.commit_weights(netuid, weights, salt)` and `reveal_weights()`. ~10 lines of wiring once a netuid is registered. |
| "Mainnet btcli sheet" | `subnet_register.py` prints commands but never executes them. | Run them. Costs ~3,000+ TAO at current burn rates. We have a hackathon-budget. |
| ~~"MockGLMClient"~~ ✅ **closed 2026-05-16** | Real `GLMClient` (Zhipu, gated on `ZHIPU_API_KEY`) AND real `AnthropicJudge` (Claude, gated on `ANTHROPIC_API_KEY`) both wired into `make_glm()` factory. Mock is now last-resort only. 3 new tests cover factory order + Anthropic round-trip. | At the event: `export ZHIPU_API_KEY=…` to switch from Claude → GLM for sponsor optics. |
| "Yuma consensus simulator" | A 200-line Python model. Real Yuma is a Rust runtime pallet with substrate-level state. | Run an actual `subtensor --chain dev` node locally (fast-block mode, 250ms blocks). Documented in the SubtensorAPI docs but takes a day to wire reliably. |
| "Per-miner outputs" | Deterministic character-dropout of the gold reference. NOT actual model outputs. | Load 3 different Hokkien Whisper checkpoints (small / medium / SeamlessM4T-v2) — get genuinely different translations. |

## What we WOULD ship if this won

In priority order, with rough effort estimates:

1. **Real Whisper / SeamlessM4T-v2 miner end-to-end** (1 day): `seamless_miner.py` is wired; remaining work is loading Common Voice `nan-tw` audio at scale and measuring per-checkpoint WER on a held-out split.
2. **Local subtensor + real registration** (2 days): `docker run subtensor/subtensor:latest --chain dev`, register on testnet, run real miner+validator extrinsics. The btcli sheet is already in `subnet_register.py`.
3. **Speaker DAO contract → mainnet** (1 day): contract + tests already exist (`contracts/`); remaining work is swapping native-ETH stake for the Subtensor EVM staking precompile.
4. **Glicko-2 calibration** (4 hours): currently defaults; measure against real annotated dataset.
5. **Recruit 5 actual Hokkien speakers** (~weeks of outreach to orgs in `partners.md`) — sign LOIs, run a tiny live trial.

## Why this is still a winning ideathon submission

The judging rubric (`产品力 / 组织力 / 验证力 / 博弈力`) explicitly weights **mechanism design over coding**.

What we have proves we understand the mechanism *enough to compile it to code*:

- Real `bt.Synapse` types prove we know the chain interface
- Real FLORES + chrF++ proves we know modern MT eval
- Glicko-2 implementation proves we know speaker-rating theory
- The attack simulator proves we know which hyperparam defeats which attack
- The btcli command sheet proves we can express our design as on-chain operations

What we *don't* have is a production deployment — and the ideathon explicitly says that's not what they're judging.

This document exists so judges who do a code-review don't catch us pretending otherwise.
