"""On-chain SpeakerDAO bridge (web3.py → deployed Solidity).

Validators can run with either backend:

  --dao-backend=json       → speaker_dao.SpeakerDAO (file-backed, default)
  --dao-backend=onchain    → speaker_dao_chain.OnChainSpeakerDAO (this module)

The on-chain version proves the mechanism is deployable. We point it at a
local Anvil node for the demo; in production this targets the Subtensor EVM
precompile space and the native TAO staking precompile (0x...0805).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from web3 import Web3
from web3.contract import Contract

CONTRACT_NAME = "SpeakerDAO"
ARTIFACT_PATH = Path(__file__).parent.parent / "contracts" / "out" / "SpeakerDAO.sol" / "SpeakerDAO.json"
DEFAULT_RPC = "http://127.0.0.1:8545"


def _load_artifact() -> dict:
    if not ARTIFACT_PATH.exists():
        raise FileNotFoundError(
            f"SpeakerDAO artifact not found at {ARTIFACT_PATH}. "
            f"Run `forge build --root contracts` first."
        )
    return json.loads(ARTIFACT_PATH.read_text())


def deploy(
    w3: Web3,
    deployer_priv_key: str,
    min_stake_wei: int = 100 * 10**18,
) -> str:
    """Deploy SpeakerDAO. Returns the deployed contract address."""
    art = _load_artifact()
    acct = w3.eth.account.from_key(deployer_priv_key)
    contract = w3.eth.contract(abi=art["abi"], bytecode=art["bytecode"]["object"])
    tx = contract.constructor(min_stake_wei).build_transaction({
        "from": acct.address,
        "nonce": w3.eth.get_transaction_count(acct.address),
        "gas": 3_000_000,
        "gasPrice": w3.eth.gas_price,
    })
    signed = acct.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    if receipt.status != 1:
        raise RuntimeError(f"SpeakerDAO deploy failed: {receipt}")
    return receipt.contractAddress


class OnChainSpeakerDAO:
    """web3.py wrapper that mirrors the off-chain SpeakerDAO API."""

    def __init__(self, w3: Web3, contract_address: str) -> None:
        art = _load_artifact()
        self._w3 = w3
        self._contract: Contract = w3.eth.contract(address=contract_address, abi=art["abi"])

    @property
    def address(self) -> str:
        return self._contract.address

    @staticmethod
    def _lang_to_bytes32(lang: str) -> bytes:
        b = lang.encode("utf-8")
        if len(b) > 32:
            raise ValueError(f"lang code too long for bytes32: {lang!r}")
        return b.ljust(32, b"\x00")

    def stake(self, priv_key: str, lang: str, amount_wei: int) -> str:
        acct = self._w3.eth.account.from_key(priv_key)
        tx = self._contract.functions.stake(self._lang_to_bytes32(lang)).build_transaction({
            "from": acct.address,
            "nonce": self._w3.eth.get_transaction_count(acct.address),
            "value": amount_wei,
            "gas": 200_000,
            "gasPrice": self._w3.eth.gas_price,
        })
        signed = acct.sign_transaction(tx)
        h = self._w3.eth.send_raw_transaction(signed.raw_transaction)
        r = self._w3.eth.wait_for_transaction_receipt(h)
        if r.status != 1:
            raise RuntimeError(f"stake() failed: {r}")
        return h.hex()

    def attest(self, attester_priv_key: str, speaker_addr: str, lang: str) -> str:
        acct = self._w3.eth.account.from_key(attester_priv_key)
        tx = self._contract.functions.attest(
            speaker_addr, self._lang_to_bytes32(lang)
        ).build_transaction({
            "from": acct.address,
            "nonce": self._w3.eth.get_transaction_count(acct.address),
            "gas": 200_000,
            "gasPrice": self._w3.eth.gas_price,
        })
        signed = acct.sign_transaction(tx)
        h = self._w3.eth.send_raw_transaction(signed.raw_transaction)
        r = self._w3.eth.wait_for_transaction_receipt(h)
        if r.status != 1:
            raise RuntimeError(f"attest() failed: {r}")
        return h.hex()

    def is_registered(self, speaker_addr: str, lang: str) -> bool:
        return bool(
            self._contract.functions.isRegistered(
                speaker_addr, self._lang_to_bytes32(lang)
            ).call()
        )

    def record_vote(
        self,
        speaker_priv_key: str,
        lang: str,
        miner_a: int,
        miner_b: int,
        winner: int,
    ) -> str:
        acct = self._w3.eth.account.from_key(speaker_priv_key)
        tx = self._contract.functions.recordVote(
            self._lang_to_bytes32(lang), miner_a, miner_b, winner
        ).build_transaction({
            "from": acct.address,
            "nonce": self._w3.eth.get_transaction_count(acct.address),
            "gas": 200_000,
            "gasPrice": self._w3.eth.gas_price,
        })
        signed = acct.sign_transaction(tx)
        h = self._w3.eth.send_raw_transaction(signed.raw_transaction)
        r = self._w3.eth.wait_for_transaction_receipt(h)
        if r.status != 1:
            raise RuntimeError(f"recordVote() failed: {r}")
        return h.hex()

    def get_rating(self, miner_uid: int, lang: str) -> int:
        """Returns rating × 1e6 (default 1500e6)."""
        return int(
            self._contract.functions.getRating(
                miner_uid, self._lang_to_bytes32(lang)
            ).call()
        )

    # ─── Compatibility shim with the JSON SpeakerDAO ────────────
    # The validator calls `dao.elo(miner_uid, lang)` and expects a float.

    def elo(self, miner_uid: int, lang: str) -> float:
        return self.get_rating(miner_uid, lang) / 1e6

    def set_rating(
        self,
        owner_priv_key: str,
        miner_uid: int,
        lang: str,
        rating_1e6: int,
    ) -> str:
        acct = self._w3.eth.account.from_key(owner_priv_key)
        tx = self._contract.functions.setRating(
            miner_uid, self._lang_to_bytes32(lang), rating_1e6
        ).build_transaction({
            "from": acct.address,
            "nonce": self._w3.eth.get_transaction_count(acct.address),
            "gas": 200_000,
            "gasPrice": self._w3.eth.gas_price,
        })
        signed = acct.sign_transaction(tx)
        h = self._w3.eth.send_raw_transaction(signed.raw_transaction)
        r = self._w3.eth.wait_for_transaction_receipt(h)
        if r.status != 1:
            raise RuntimeError(f"setRating() failed: {r}")
        return h.hex()


def connect(rpc_url: str = DEFAULT_RPC) -> Web3:
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        raise ConnectionError(
            f"Cannot reach RPC at {rpc_url}. Start anvil with: anvil --port 8545"
        )
    return w3
