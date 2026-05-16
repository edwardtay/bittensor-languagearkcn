"""Glicko-2 rating system for native-speaker pairwise votes.

Why Glicko-2 over plain Elo:
- Handles uncertainty (RD = rating deviation) → new miners aren't penalized
- Volatility parameter σ → models genuinely improving miners vs noise
- Inactivity decay → speakers who stop voting don't gain weight forever

Reference: Glickman, M. (2012). "Example of the Glicko-2 system."
http://www.glicko.net/glicko/glicko2.pdf
"""
from __future__ import annotations

import math
from dataclasses import dataclass

# Glicko-2 constants
TAU = 0.5          # System volatility constraint (small = more stable)
EPSILON = 1e-6
SCALE = 173.7178   # Glicko-1 → Glicko-2 rating scale conversion
INITIAL_RATING = 1500.0
INITIAL_RD = 350.0
INITIAL_VOLATILITY = 0.06


@dataclass
class Rating:
    rating: float = INITIAL_RATING
    rd: float = INITIAL_RD               # rating deviation
    volatility: float = INITIAL_VOLATILITY

    def to_glicko2(self) -> tuple[float, float]:
        return ((self.rating - INITIAL_RATING) / SCALE, self.rd / SCALE)


@dataclass
class Match:
    """A single pairwise comparison from a native speaker."""

    opponent_rating: float
    opponent_rd: float
    outcome: float  # 1.0 = miner won, 0.0 = miner lost, 0.5 = draw


def _g(rd: float) -> float:
    return 1.0 / math.sqrt(1.0 + 3.0 * rd * rd / (math.pi * math.pi))


def _E(mu: float, mu_j: float, phi_j: float) -> float:
    return 1.0 / (1.0 + math.exp(-_g(phi_j) * (mu - mu_j)))


def update_rating(rating: Rating, matches: list[Match]) -> Rating:
    """Apply Glicko-2 update step. Pure function — returns new Rating."""
    if not matches:
        # No matches → only RD increases (uncertainty grows)
        phi = rating.rd / SCALE
        new_phi = math.sqrt(phi * phi + rating.volatility * rating.volatility)
        return Rating(
            rating=rating.rating,
            rd=min(INITIAL_RD, new_phi * SCALE),
            volatility=rating.volatility,
        )

    mu, phi = rating.to_glicko2()

    # Step 3: estimated variance v
    v_inv = 0.0
    for m in matches:
        mu_j = (m.opponent_rating - INITIAL_RATING) / SCALE
        phi_j = m.opponent_rd / SCALE
        g_j = _g(phi_j)
        E_j = _E(mu, mu_j, phi_j)
        v_inv += g_j * g_j * E_j * (1 - E_j)
    v = 1.0 / v_inv

    # Step 4: estimated improvement Δ
    delta = 0.0
    for m in matches:
        mu_j = (m.opponent_rating - INITIAL_RATING) / SCALE
        phi_j = m.opponent_rd / SCALE
        E_j = _E(mu, mu_j, phi_j)
        delta += _g(phi_j) * (m.outcome - E_j)
    delta *= v

    # Step 5: new volatility via Illinois algorithm
    a = math.log(rating.volatility * rating.volatility)

    def f(x: float) -> float:
        ex = math.exp(x)
        denom = 2.0 * (phi * phi + v + ex) ** 2
        return (ex * (delta * delta - phi * phi - v - ex)) / denom - (x - a) / (TAU * TAU)

    A = a
    if delta * delta > phi * phi + v:
        B = math.log(delta * delta - phi * phi - v)
    else:
        k = 1
        while f(a - k * TAU) < 0:
            k += 1
        B = a - k * TAU
    fA, fB = f(A), f(B)
    while abs(B - A) > EPSILON:
        C = A + (A - B) * fA / (fB - fA)
        fC = f(C)
        if fC * fB < 0:
            A, fA = B, fB
        else:
            fA /= 2.0
        B, fB = C, fC
    new_volatility = math.exp(A / 2.0)

    # Step 6: pre-rating-period RD
    phi_star = math.sqrt(phi * phi + new_volatility * new_volatility)

    # Step 7: new RD and rating
    new_phi = 1.0 / math.sqrt(1.0 / (phi_star * phi_star) + 1.0 / v)
    new_mu = mu + new_phi * new_phi * sum(
        _g(m.opponent_rd / SCALE) * (m.outcome - _E(mu, (m.opponent_rating - INITIAL_RATING) / SCALE, m.opponent_rd / SCALE))
        for m in matches
    )

    return Rating(
        rating=new_mu * SCALE + INITIAL_RATING,
        rd=new_phi * SCALE,
        volatility=new_volatility,
    )
