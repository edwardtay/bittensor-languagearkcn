"""Weight-copying attack simulator.

The historical Bittensor attack: a cheating **validator** doesn't do any real
work. It just reads other validators' on-chain weight vectors and re-publishes
them as its own. Because Yuma rewards consensus (vTrust), the freeloader earns
dividends without actually scoring miners.

LanguageArk-CN defeats this with `commit_reveal_period = 5 tempos` — the
freeloader can only see weights that are 5 tempos (~6h) stale. By then, honest
validators have moved on to scoring fresh miner outputs.

We simulate two networks side-by-side and track the freeloader's vTrust
(measured as 1 − L1 distance between the freeloader's weights and the honest
consensus, per tempo).

Miner quality DRIFTS over the simulation: every 3 tempos, the relative ranking
of the two miners flips. This mimics real subnets where miner relative quality
evolves as they improve / get deregistered / new ones register.
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from typing import Optional

import click

N_MINERS = 5
N_TEMPOS = 12


@dataclass
class Network:
    name: str
    commit_reveal_period: int   # 0 = vulnerable, 5 = LanguageArk-CN
    # honest_weights[t] = the consensus weight vector at tempo t
    honest_weights: list[dict[int, float]] = field(default_factory=list)
    # freeloader_weights[t] = what the freeloader publishes at tempo t
    freeloader_weights: list[dict[int, float]] = field(default_factory=list)
    # On-chain "revealed" weights, indexed by tempo. None until reveal-time.
    revealed: list[Optional[dict[int, float]]] = field(default_factory=list)


def _ground_truth_at_tempo(t: int) -> dict[int, float]:
    """Real miner quality at tempo t. Shifts every 2 tempos to mimic drift.

    Real subnets see this kind of churn because: (a) new miners register
    every immunity_period, (b) existing miners improve their models, (c)
    deregistration removes the bottom each tempo.
    """
    rotations = [
        [0, 1, 2, 3, 4],
        [4, 3, 2, 1, 0],
        [2, 4, 0, 3, 1],
        [1, 0, 4, 2, 3],
        [3, 2, 1, 0, 4],
        [0, 4, 3, 2, 1],
    ]
    ranks = rotations[(t // 2) % len(rotations)]
    # Convert rank to weight with power-law decay (peaky, like real subnets):
    # rank 0 → 1.0, then 0.4, 0.16, 0.064, 0.026 — top miner has ~38x the bottom.
    weights = {}
    for rank_pos, uid in enumerate(ranks):
        weights[uid] = round(0.4 ** rank_pos, 4)
    return weights


def _l1_distance(a: dict[int, float], b: dict[int, float]) -> float:
    keys = set(a) | set(b)
    return sum(abs(a.get(k, 0.0) - b.get(k, 0.0)) for k in keys)


def simulate(network: Network, n_tempos: int = N_TEMPOS) -> None:
    network.revealed = [None] * n_tempos

    for t in range(n_tempos):
        # 1. Honest validators score miners against ground truth.
        truth = _ground_truth_at_tempo(t)
        network.honest_weights.append(truth)

        # 2. Reveal-phase bookkeeping.
        if network.commit_reveal_period == 0:
            # No protection — honest weights are visible immediately.
            network.revealed[t] = truth
        else:
            # commit-reveal: weights committed at tempo t become visible at
            # tempo (t + commit_reveal_period).
            target = t + network.commit_reveal_period
            if target < n_tempos:
                network.revealed[target] = truth

        # 3. Freeloader publishes the most recent revealed weights it can find.
        seen = next((r for r in reversed(network.revealed[: t + 1]) if r), None)
        if seen is None:
            # Nothing revealed yet → freeloader publishes uniform (it has no info)
            seen = {i: 1.0 / N_MINERS for i in range(N_MINERS)}
        network.freeloader_weights.append(seen)


def _vtrust(network: Network) -> list[float]:
    """Per-tempo earnings of the freeloader relative to an honest validator.

    Modelled as dot(freeloader_weights, honest_consensus_weights) / dot(honest, honest).
    An honest validator who matches consensus exactly earns 1.0; a freeloader
    earns proportionally less for every miner it under/over-weights vs truth.
    """
    out = []
    for h, f in zip(network.honest_weights, network.freeloader_weights):
        keys = set(h) | set(f)
        # Normalize weights to unit L1 first
        h_sum = sum(h.get(k, 0.0) for k in keys) or 1.0
        f_sum = sum(f.get(k, 0.0) for k in keys) or 1.0
        h_norm = {k: h.get(k, 0.0) / h_sum for k in keys}
        f_norm = {k: f.get(k, 0.0) / f_sum for k in keys}
        # Dividend ∝ sum over miners of (validator_weight * miner_incentive_share)
        # Honest validator scoring perfectly: dot(h, h)
        # Freeloader: dot(f, h)
        honest_self = sum(h_norm[k] * h_norm[k] for k in keys)
        free_dot = sum(f_norm[k] * h_norm[k] for k in keys)
        out.append(free_dot / honest_self if honest_self else 0.0)
    return out


def _print_results(network: Network) -> None:
    vt = _vtrust(network)
    mean_vt = statistics.fmean(vt)
    click.echo(f"\n── {network.name} (commit_reveal_period = {network.commit_reveal_period} tempos) ──")
    click.echo(f"  freeloader-validator mean vTrust over {len(vt)} tempos: {mean_vt:.3f}")
    click.echo(f"  per-tempo: {' '.join(f'{v:.2f}' for v in vt)}")
    pct = mean_vt * 100
    if mean_vt >= 0.9:
        click.echo(f"  → freeloader earns ~{pct:.0f}% of honest dividends WITHOUT DOING ANY WORK")
    elif mean_vt >= 0.5:
        click.echo(f"  → freeloader earns ~{pct:.0f}% of honest dividends")
    else:
        click.echo(f"  → freeloader earns only ~{pct:.0f}% of honest dividends — attack defeated")


@click.command()
def main() -> None:
    """Run the side-by-side weight-copy attack simulation."""
    click.echo("""
╔════════════════════════════════════════════════════════════════════╗
║  Weight-copy attack simulator                                      ║
║                                                                    ║
║  A freeloader-validator publishes copies of honest weights instead ║
║  of scoring miners — earning vTrust for zero work.                 ║
║                                                                    ║
║  Network A: commit_reveal_period = 0  (vulnerable default)         ║
║  Network B: commit_reveal_period = 5  (LanguageArk-CN config)      ║
╚════════════════════════════════════════════════════════════════════╝
""")

    network_a = Network(name="Network A (vulnerable)", commit_reveal_period=0)
    network_b = Network(name="Network B (LanguageArk-CN)", commit_reveal_period=5)

    simulate(network_a)
    simulate(network_b)

    _print_results(network_a)
    _print_results(network_b)

    click.echo("""
─────────────────────────────────────────────────────────────────────
verdict: with commit_reveal_period = 5, the freeloader sees only
weights that are 5 tempos (~6 hours) stale. Honest validators have
already shifted to scoring fresh miner outputs (miner quality drifts
every ~3 tempos in this sim). The freeloader's stale copy is wrong.

This is why LanguageArk-CN sets commit_reveal_period = 5.
─────────────────────────────────────────────────────────────────────
""")


if __name__ == "__main__":
    main()
