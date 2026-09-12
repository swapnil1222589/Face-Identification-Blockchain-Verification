import json
import os
from pathlib import Path

from solcx import compile_standard, install_solc
from web3 import Web3

ROOT = Path(__file__).resolve().parents[1]
SOL = ROOT / "contracts" / "ContentVerifier.sol"
ART = ROOT / "artifacts"
ART.mkdir(exist_ok=True)

ROOT = Path(__file__).resolve().parents[1] SOL = ROOT / "contracts" / "ContentVerifier.sol" ART = ROOT / "artifacts" ART.mkdir(exist_ok=True)

RPC_URL = os.environ["RPC_URL"]
PRIVATE_KEY = os.environ["PRIVATE_KEY"]

install_solc("0.8.24")
source = SOL.read_text(encoding="utf-8")
compiled = compile_standard(
    {
        "language": "Solidity",
        "sources": {"ContentVerifier.sol": {"content": source}},
        "settings": {"outputSelection": {"*": {"*": ["abi", "evm.bytecode.object"]}}},
    },
    solc_version="0.8.24",
)
contract_data = compiled["contracts"]["ContentVerifier.sol"]["ContentVerifier"]
abi = contract_data["abi"]
bytecode = contract_data["evm"]["bytecode"]["object"]

(ART / "ContentVerifier.abi.json").write_text(json.dumps(abi, indent=2), encoding="utf-8")
(ART / "ContentVerifier.bytecode.txt").write_text(bytecode, encoding="utf-8")

w3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={"timeout": 30}))
if not w3.is_connected():
    raise RuntimeError("RPC connection failed.")

account = w3.eth.account.from_key(PRIVATE_KEY)
contract = w3.eth.contract(abi=abi, bytecode=bytecode)
nonce = w3.eth.get_transaction_count(account.address, "pending")
tx = contract.constructor().build_transaction({
    "from": account.address,
    "nonce": nonce,
    "chainId": w3.eth.chain_id,
    "gas": 1_500_000,
    "maxFeePerGas": w3.to_wei(30, "gwei"),
    "maxPriorityFeePerGas": w3.to_wei(1, "gwei"),
})
signed = account.sign_transaction(tx)
tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)

print("Chain ID:", w3.eth.chain_id)
print("Deployer:", account.address)
print("Contract:", receipt.contractAddress)
print("Deployment TX:", receipt.transactionHash.hex())
print()
print("Set CONTRACT_ADDRESS to:", receipt.contractAddress)
