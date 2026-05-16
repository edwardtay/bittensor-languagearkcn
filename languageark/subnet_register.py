"""Print the exact `btcli` commands to register LanguageArk-CN on mainnet.

We don't execute the call here — registering a subnet burns 3,000+ TAO and we
don't want a hackathon accident. But we generate the full sequence so judges
can see we know the chain interface, and a non-demo run can copy-paste.

Reference: docs.learnbittensor.org/subnets/subnet-creation
"""
from __future__ import annotations

import click

# Our chosen hyperparameters, translated to btcli flags + u16/u64 chain units.
HYPERPARAMS = {
    "tempo":               (360,      "blocks (~72 min per epoch)"),
    "immunity_period":     (5_000,    "blocks (~16.6h) — new neurons protected"),
    "activity_cutoff":     (5_000,    "blocks — validators inactive longer than this are dropped"),
    "kappa":               (39_320,   "u16 (≈0.6) — raised above default 32767 to need >60% stake for cabal"),
    "alpha_low":           (3_277,    "u16 (≈0.05) — tight bond floor"),
    "alpha_high":          (22_937,   "u16 (≈0.35) — tight bond ceiling, defeats whipsaw"),
    "bonds_moving_avg":    (900_000,  "EMA inertia for bonds"),
    "min_allowed_weights": (16,       "forces weight spread across ≥16 miners — kills single-miner cabal"),
    "max_weights_limit":   (65_535,   "u16 max — per-miner weight cap"),
    "weights_rate_limit":  (100,      "blocks min between weight-set extrinsics per validator"),
    "commit_reveal_period":(5,        "tempos (~6h reveal lag) — defeats weight-copy attacks"),
    "min_burn":            (500_000,  "rao (0.0005 TAO) — floor on dynamic burn"),
    "max_burn":            (100_000_000_000, "rao (100 TAO) — ceiling on dynamic burn"),
}


@click.command()
@click.option("--wallet", default="languageark", help="coldkey wallet name")
@click.option("--hotkey", default="owner", help="subnet owner hotkey name")
@click.option("--network", default="finney", type=click.Choice(["finney", "test"]))
def main(wallet: str, hotkey: str, network: str) -> None:
    click.echo(f"""
═══════════════════════════════════════════════════════════════════════
  LanguageArk-CN — mainnet registration command sheet
  Network: {network}      Wallet: {wallet}      Hotkey: {hotkey}
═══════════════════════════════════════════════════════════════════════

⚠️  Subnet creation currently burns ~3,000+ TAO. Confirm live cost first:
   btcli subnet list --network {network}

──────────────────────────────────────────────────────────────────────
STEP 1 — Create the subnet
──────────────────────────────────────────────────────────────────────
btcli subnet create \\
    --network {network} \\
    --wallet.name {wallet} \\
    --wallet.hotkey {hotkey}

# Output: NETUID=<new>. Note this number.

──────────────────────────────────────────────────────────────────────
STEP 2 — Set our chosen hyperparameters
──────────────────────────────────────────────────────────────────────""")

    for name, (value, comment) in HYPERPARAMS.items():
        click.echo(
            f"btcli sudo set --network {network} --netuid <NETUID> \\\n"
            f"    --param {name} --value {value}    # {comment}"
        )

    click.echo(f"""
──────────────────────────────────────────────────────────────────────
STEP 3 — Stake the owner hotkey (so we can vote / propose)
──────────────────────────────────────────────────────────────────────
btcli stake add \\
    --network {network} \\
    --wallet.name {wallet} \\
    --wallet.hotkey {hotkey} \\
    --amount 1000           # 1000 TAO for governance presence

──────────────────────────────────────────────────────────────────────
STEP 4 — Publish subnet metadata
──────────────────────────────────────────────────────────────────────
btcli subnet metadata set --netuid <NETUID> \\
    --github   https://github.com/edwardtay/bittensor-languagearkcn \\
    --discord  https://discord.gg/languageark \\
    --homepage https://languageark.cn \\
    --description "Endangered Chinese-language preservation; Hokkien v1"

──────────────────────────────────────────────────────────────────────
STEP 5 — Bootstrap the speaker DAO (off-chain)
──────────────────────────────────────────────────────────────────────
python -m languageark.cli_bootstrap     # registers Xiamen + Taiwan + Penang speakers

──────────────────────────────────────────────────────────────────────
STEP 6 — Start a validator
──────────────────────────────────────────────────────────────────────
python -m languageark.validator --netuid <NETUID> --lang nan

──────────────────────────────────────────────────────────────────────
What we DON'T do at registration
──────────────────────────────────────────────────────────────────────
• Don't enable liquid-α until 2 tempos after launch — gives miners stable
  bonds to start.
• Don't set `min_allowed_weights = 16` until ≥20 miners have registered.
• Don't unlock commit-reveal `commit_reveal_period` for the first epoch
  (chain limitation — period applies from tempo 2 onward).
""")


if __name__ == "__main__":
    main()
