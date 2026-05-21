"""E2E local-anvil deploy + smoke-test of the SpeakerDAO contract.

Requires: `anvil --port 8545` running. Uses anvil's deterministic default
accounts so no setup is needed.

Run:  python scripts/deploy_speaker_dao_local.py
"""
from __future__ import annotations

import sys
from typing import Final

from languageark.speaker_dao_chain import OnChainSpeakerDAO, connect, deploy

# Anvil deterministic test keys (well-known; never use on mainnet).
ANVIL_KEYS: Final[list[str]] = [
    "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80",  # owner
    "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d",  # speaker
    "0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a",  # attester A
    "0x7c852118294e51e653712a81e05800f419141751be58f605c371e15141b007a6",  # attester B
]


def main() -> int:
    w3 = connect()
    owner_key, speaker_key, attA_key, attB_key = ANVIL_KEYS

    def addr(k: str) -> str:
        return w3.eth.account.from_key(k).address

    print(f"chain_id = {w3.eth.chain_id}, head = {w3.eth.block_number}")
    print(f"owner     = {addr(owner_key)}")
    print(f"speaker   = {addr(speaker_key)}")
    print(f"attester A= {addr(attA_key)}")
    print(f"attester B= {addr(attB_key)}")

    print("\n[1/5] deploying SpeakerDAO with minStake = 100 ETH...")
    contract_addr = deploy(w3, owner_key, min_stake_wei=100 * 10**18)
    print(f"      ✓ deployed at {contract_addr}")

    dao = OnChainSpeakerDAO(w3, contract_addr)

    print("\n[2/5] speaker stakes 100 ETH for lang='nan'...")
    h = dao.stake(speaker_key, "nan", 100 * 10**18)
    print(f"      ✓ tx {h[:18]}...   isRegistered? {dao.is_registered(addr(speaker_key), 'nan')}")

    print("\n[3/5] attester A attests...")
    dao.attest(attA_key, addr(speaker_key), "nan")
    print(f"      isRegistered? {dao.is_registered(addr(speaker_key), 'nan')}  (need 2)")

    print("\n[4/5] attester B attests...")
    dao.attest(attB_key, addr(speaker_key), "nan")
    is_reg = dao.is_registered(addr(speaker_key), "nan")
    print(f"      ✓ isRegistered? {is_reg}")
    if not is_reg:
        return 1

    print("\n[5/5] speaker records vote: miner 7 beats miner 3 on 'nan'...")
    dao.record_vote(speaker_key, "nan", miner_a=7, miner_b=3, winner=7)
    print("      ✓ vote on-chain")

    print("\n      owner writes Glicko-2 rating 1620 for miner 7...")
    dao.set_rating(owner_key, miner_uid=7, lang="nan", rating_1e6=1620 * 10**6)
    print(f"      getRating(7,nan) = {dao.get_rating(7, 'nan') / 1e6:.2f}")
    print(f"      getRating(3,nan) = {dao.get_rating(3, 'nan') / 1e6:.2f} (default)")

    print("\n✅  Speaker DAO is REAL on-chain. Mechanism works e2e.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
