"""Full e2e: deploy SpeakerDAO → seed ratings → run validator against it.

Requires `anvil --port 8545` running. Proves the validator can read miner
Glicko ratings from a real deployed contract instead of a JSON shim.
"""
from __future__ import annotations

import os
import subprocess
import sys

from languageark.speaker_dao_chain import OnChainSpeakerDAO, connect, deploy

OWNER_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"


def main() -> int:
    w3 = connect()
    print(f"[setup] connected to {w3.provider.endpoint_uri}  chain_id={w3.eth.chain_id}")

    print("[setup] deploying SpeakerDAO …")
    addr = deploy(w3, OWNER_KEY, min_stake_wei=100 * 10**18)
    print(f"[setup] ✓ contract at {addr}")

    dao = OnChainSpeakerDAO(w3, addr)
    print("[setup] seeding on-chain Glicko ratings: uid0=1751, uid1=1481, uid2=1243 (nan)")
    dao.set_rating(OWNER_KEY, 0, "nan", 1751 * 10**6)
    dao.set_rating(OWNER_KEY, 1, "nan", 1481 * 10**6)
    dao.set_rating(OWNER_KEY, 2, "nan", 1243 * 10**6)
    print(f"[setup]   read-back uid0={dao.elo(0, 'nan'):.0f}  uid1={dao.elo(1, 'nan'):.0f}  uid2={dao.elo(2, 'nan'):.0f}")

    print("\n[run] launching validator with --dao-backend=onchain ...\n")
    cmd = [
        sys.executable, "-m", "languageark.validator",
        "--eval-set", "hokkien",
        "--dao-backend", "onchain",
        "--dao-rpc", "http://127.0.0.1:8545",
        "--dao-contract", addr,
    ]
    rc = subprocess.call(cmd)
    return rc


if __name__ == "__main__":
    sys.exit(main())
