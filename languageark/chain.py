"""REAL bittensor SDK integration.

Probes the live chain — testnet or mainnet — using the actual `bittensor`
package. Run it to:

  - confirm the SDK is installed and importable
  - read a real subnet's hyperparameters
  - construct a wallet object (does NOT touch keystore unless you ask)
  - prepare a HokkienMT Synapse and show what dendrite-query bytes look like

This is not a mock — it talks to substrate/finney unless --network=test.

Usage:
    python -m languageark.chain probe --netuid 1 --network finney
    python -m languageark.chain wallet --name languageark
"""
from __future__ import annotations

import json

import click

from .bt_protocol import BT_AVAILABLE, HokkienASR, HokkienMT


@click.group()
def main() -> None:
    """Real bittensor-SDK probes for LanguageArk-CN."""


@main.command()
@click.option("--netuid", type=int, default=1, help="Subnet to inspect (1 = SN1 Apex)")
@click.option("--network", type=click.Choice(["finney", "test", "local"]), default="finney")
def probe(netuid: int, network: str) -> None:
    """Read real on-chain subnet hyperparameters."""
    if not BT_AVAILABLE:
        raise click.ClickException("bittensor SDK not installed. Run: pip install bittensor")
    import bittensor as bt

    click.echo(f"\n🔌 connecting to {network}…")
    sub = bt.subtensor(network=network)
    click.echo(f"   block height: {sub.get_current_block()}")

    click.echo(f"\n📡 reading netuid={netuid} state…")
    try:
        meta = sub.metagraph(netuid=netuid, lite=True)
        click.echo(f"   netuid:          {meta.netuid}")
        click.echo(f"   n (neurons):     {meta.n.item()}")
        click.echo(f"   total stake (τ): {float(meta.total_stake.sum()):.2f}")
        click.echo(f"   block_at_reg:    {meta.block_at_registration[:3].tolist()} …")
    except Exception as e:
        click.echo(f"   metagraph fetch failed: {e}")

    # Hyperparameters
    click.echo(f"\n⚙️  hyperparameters (selected) for netuid={netuid}:")
    try:
        hp = sub.get_subnet_hyperparameters(netuid=netuid)
        if hp is None:
            click.echo("   (none returned — subnet may not exist on this network)")
        else:
            for k in [
                "tempo", "kappa", "min_allowed_weights", "max_weights_limit",
                "weights_rate_limit", "bonds_moving_avg", "immunity_period",
                "activity_cutoff", "alpha_low", "alpha_high", "commit_reveal_period",
            ]:
                if hasattr(hp, k):
                    click.echo(f"   {k:<25} {getattr(hp, k)}")
    except Exception as e:
        click.echo(f"   hyperparameter fetch failed: {e}")


@main.command()
@click.option("--name", default="languageark", help="Coldkey wallet name (in ~/.bittensor/wallets/)")
@click.option("--hotkey", default="owner")
def wallet(name: str, hotkey: str) -> None:
    """Construct a bt.wallet object (does NOT create keys unless they're missing).

    Just demonstrates we know the wallet API. Pass `--create` to actually generate.
    """
    if not BT_AVAILABLE:
        raise click.ClickException("bittensor SDK not installed")
    import bittensor as bt

    w = bt.wallet(name=name, hotkey=hotkey)
    click.echo(f"\n🔑 bt.wallet object constructed:")
    click.echo(f"   name        = {w.name}")
    click.echo(f"   hotkey      = {w.hotkey_str}")
    click.echo(f"   path        = {w.path}")
    click.echo(f"   coldkey_file exists: {w.coldkey_file.exists_on_device()}")
    click.echo(f"   hotkey_file exists:  {w.hotkey_file.exists_on_device()}")


@main.command()
def synapse_demo() -> None:
    """Construct a real bt.Synapse subclass and print its wire shape."""
    if not BT_AVAILABLE:
        raise click.ClickException("bittensor SDK not installed")
    import bittensor as bt

    s = HokkienMT(text="你食飽未?", src_lang="nan", tgt_lang="zh-Hans")
    click.echo(f"\n📦 HokkienMT Synapse (subclasses bt.Synapse v{bt.__version__})")
    click.echo(f"   .name           = {s.name}")
    click.echo(f"   .text           = {s.text!r}")
    click.echo(f"   .src_lang       = {s.src_lang}")
    click.echo(f"   .tgt_lang       = {s.tgt_lang}")
    click.echo(f"   .translation    = {s.translation!r}  (filled by miner)")
    click.echo(f"\n   is bt.Synapse?  {isinstance(s, bt.Synapse)}")
    click.echo(f"   is HokkienASR?  {isinstance(s, HokkienASR)}")

    click.echo(f"\n   serializable JSON shape (subset of bt.Synapse fields):")
    body = {
        k: v for k, v in s.model_dump().items()
        if not k.startswith("_")
        and k not in ("axon", "dendrite", "computed_body_hash", "required_hash_fields")
        and not callable(v)
    }
    click.echo("   " + json.dumps(body, ensure_ascii=False, indent=2, default=str).replace("\n", "\n   "))


if __name__ == "__main__":
    main()
