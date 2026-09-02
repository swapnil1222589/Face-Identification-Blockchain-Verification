import pytest

from app.blockchain import BlockchainError, get_blockchain_config


def test_blockchain_config_requires_rpc(monkeypatch):
    monkeypatch.delenv("RPC_URL", raising=False)
    monkeypatch.delenv("PRIVATE_KEY", raising=False)
    monkeypatch.delenv("CONTRACT_ADDRESS", raising=False)
    with pytest.raises(BlockchainError):
        get_blockchain_config()
