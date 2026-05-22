# OPS — how this subnet actually runs

Concise operator-facing notes. Pairs with [`HONESTY.md`](HONESTY.md) (what's real) and [`whitepaper.md`](whitepaper.md) (why).

## 1. Roles

| Role | Stake | Daily job | Failure mode |
|---|---|---|---|
| **Subnet owner** | one-time registration burn (~3,000 TAO at finney) | Bumps hyperparams via `btcli sudo`; rotates eval set weekly | Owner key loss → subnet stuck on old eval. Mitigation: 2-of-3 multisig on owner hotkey. |
| **Validator** (≥10k TAO) | TAO stake + bond | Pulls miner outputs each tempo; commits sealed weights; reveals after 5 tempos | Goes offline → vTrust decays, emissions stop. Restart ≤2 tempos to keep bonds. |
| **Miner** | registration burn only | Serves ASR / MT / TTS over axon | Wrong-script output → 0 chrF++; back-translation BLEU ≪ 0.3 → bottom decile → deregistered next immunity window. |
| **Native-speaker DAO member** | 100 TAO + 2-of-3 attestation | Casts pairwise Elo votes; sets ratings | Sybil → slashed via `SpeakerDAO.slash()` (forge-tested). |
| **Buyer** | USD or TAO | Subscribes to dataset snapshots / model checkpoints | None — pull-based. |

## 2. Tempos & timing

- 1 tempo = **360 blocks ≈ 72 min** (finney 12s blocks).
- Commit-reveal window = **5 tempos ≈ 6 h**. Validators MUST keep their salt-keyed weight commits for that window or forfeit emission.
- Eval set rotation: **weekly** (owner publishes new FLORES held-out + curated pair set, hash on-chain).

## 3. Runbook (validator)

```bash
# one-time
git clone … && cd bittensor-languagearkcn && uv sync --extra chain
btcli wallet new_coldkey --wallet.name validator
btcli wallet new_hotkey  --wallet.name validator --wallet.hotkey default
btcli subnet register   --wallet.name validator --netuid <NETUID> --network finney
btcli stake add         --wallet.name validator --amount 10000 --netuid <NETUID>

# per-tempo loop (systemd unit recommended)
.venv/bin/python -m languageark.validator \
  --network finney --netuid <NETUID> \
  --eval-set hokkien --commit-reveal --tempo-seconds 4320
```

**Health checks:** vTrust > 0.7, emission > 0, last-reveal ≤ 5 tempos ago.
**Pager triggers:** vTrust < 0.5 for ≥2 tempos, reveal failure (lost salt), RPC > 3 consecutive timeouts.

## 4. Runbook (miner)

```bash
uv sync --extra miner            # pulls torch + transformers + seamless
.venv/bin/python -m languageark.seamless_miner --device cuda:0 --port 8091
```

GPU sizing: SeamlessM4T-v2-large = **9.5 GB VRAM** (fits on a single RTX 3090 / A10G). NLLB-200-distilled-600M = 2.5 GB. Whisper-small = 1 GB.

## 5. Cost model (single validator, 1 month, finney)

| Item | Qty | Unit | Monthly |
|---|---:|---:|---:|
| Registration burn (amortized 12 mo) | 1 | 3,000 TAO / 12 | ~250 TAO |
| Cloud VM (4 vCPU, 16 GB) | 720 h | $0.10 | **$72** |
| LLM judge — pick one: Zhipu GLM-4.6 (sponsor credits at event) | 30k | 0 | **$0** |
| or Qwen-max / Kimi / DeepSeek (Chinese API, similar pricing) | 30k | ~$0.002/1k | ~**$60** |
| or Claude Code via Max subscription (~$200/mo flat) | 30k | flat | **$0 marginal** |
| or Anthropic Claude API (haiku-4.5, fallback) | 30k | $0.001/1k | ~**$30** |
| Egress (chain RPC, ~5 GB) | 5 GB | $0.09 | **$0.50** |
| **Total cash** (excluding TAO opportunity cost) | | | **~$160 / mo** |

Miner side is dominated by GPU rental: A10G spot ≈ $0.30/h ≈ **$220/mo** continuous.

## 6. Incident playbooks

**Validator hotkey compromised.** `btcli wallet new_hotkey`, then `btcli subnet pow_register` from coldkey to swap hotkey on the existing UID. Emission resumes next tempo. Cold stake never moves.

**Lost salt before reveal.** That tempo's weights are forfeit (0 emission for that window). No further damage; commit a fresh salt next tempo.

**Speaker DAO Sybil detected.** Any 2 existing members call `SpeakerDAO.slash(addr, reason)`. Stake burns; rating writebacks from that addr are rejected by the validator (on-chain check).

**FLORES eval leaked to miners.** Owner rotates to next held-out partition immediately via `btcli sudo set_hyperparameter` pointing to new corpus hash. Miners trained on leaked split get a 1-tempo grace then drop in score.

**Subtensor RPC outage.** Validator falls back to read-only metagraph cache (60 min TTL). If outage > 2 tempos, abort commit and resume after recovery (no slash — Yuma is permissive on missed commits, only penalizes wrong reveals).

## 7. Observability

Minimum metrics to scrape (any Prometheus):

```
languageark_vtrust{netuid="…",hotkey="…"}        gauge
languageark_emission_tao{…}                       counter
languageark_last_reveal_block{…}                  gauge
languageark_miner_chrf{miner_uid="…"}             gauge
languageark_glm_call_latency_seconds              histogram
languageark_speaker_dao_active                    gauge
```

Validator logs to stdout in JSON; ship via vector → Loki. One Grafana dashboard is enough — vTrust + emission + per-miner chrF heat map.

## 8. Speaker DAO operations

- Onboarding: candidate stakes 100 TAO → 3 existing members verify off-chain (video call in Hokkien) → 2 of them call `attest(addr)` → 3rd attestation auto-triggers `register`.
- Voting cadence: 20 pairs/week minimum to remain in good standing; missing 3 weeks → cooling period (no emissions credit) until catch-up.
- Geographic distribution: target ≤ 40% from any one of {Fujian, Taiwan, SG/MY/PH/ID diaspora, NA diaspora} to defeat regional cabal.

## 9. Local dev stack

```bash
docker compose up        # static site on :8080
# in another shell:
bash demo.sh             # 7-step end-to-end (no chain, no GPU)
cd contracts && forge test       # Solidity (8 tests)
.venv/bin/pytest -q              # Python (57 tests)
```

For a real local subtensor + miner + validator triangle, see `scripts/validator_e2e_onchain.py` (requires `subtensor --chain dev` running on `:9944`).
