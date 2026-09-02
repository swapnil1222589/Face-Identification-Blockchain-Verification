from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from web3 import Web3
from web3.exceptions import ContractLogicError


class BlockchainError(RuntimeError):
    pass


def _secret(name: str) -> str | None:
    value = os.getenv(name)
    if value:
        return value
    try:
        from google.colab import userdata  # type: ignore
        return userdata.get(name)
    except Exception:
        return None


def get_blockchain_config() -> dict[str, str]:
    rpc_url = _secret("RPC_URL")
    private_key = _secret("PRIVATE_KEY")
    contract_address = _secret("CONTRACT_ADDRESS")
    if not rpc_url:
        raise BlockchainError("RPC_URL is missing.")
    if not private_key:
        raise BlockchainError("PRIVATE_KEY is missing.")
    if not contract_address:
        raise BlockchainError("CONTRACT_ADDRESS is missing.")
    return {
        "rpc_url": rpc_url,
        "private_key": private_key,
        "contract_address": contract_address,
    }


def load_abi(path: str | Path) -> list[dict[str, Any]]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


class ContentVerifierClient:
    def __init__(self, *, rpc_url: str, private_key: str, contract_address: str, abi: list[dict[str, Any]]):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 30}))
        if not self.w3.is_connected():
            raise BlockchainError("Could not connect to RPC endpoint.")

        self.account = self.w3.eth.account.from_key(private_key)
        self.contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(contract_address),
            abi=abi,
        )

    def _tx(self, fn):
        nonce = self.w3.eth.get_transaction_count(self.account.address, "pending")
        tx = fn.build_transaction({
            "from": self.account.address,
            "nonce": nonce,
            "chainId": self.w3.eth.chain_id,
            "gas": 350_000,
            "maxFeePerGas": self.w3.to_wei(30, "gwei"),
            "maxPriorityFeePerGas": self.w3.to_wei(1, "gwei"),
        })
        signed = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        return self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)

    def register(self, content_hash_hex: str, source_url: str) -> str:
        content_hash = bytes.fromhex(content_hash_hex.removeprefix("0x"))
        receipt = self._tx(self.contract.functions.registerContent(content_hash, source_url))
        return receipt.transactionHash.hex()

    def verify(self, content_hash_hex: str) -> dict[str, Any]:
        content_hash = bytes.fromhex(content_hash_hex.removeprefix("0x"))
        exists = self.contract.functions.verifyContent(content_hash).call()
        record = self.contract.functions.getRecord(content_hash).call()
        # Tuple order follows ContentVerifier.sol.
        return {
            "exists": bool(exists),
            "source_url": record[0],
            "timestamp": int(record[1]),
            "submitter": record[2],
        }
