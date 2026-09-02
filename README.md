Deployment helper
=================

In Colab, run the deployment cell from the notebook or use this sequence:

1. Install `py-solc-x`.
2. Install Solidity compiler 0.8.24.
3. Compile `contracts/ContentVerifier.sol`.
4. Deploy with your Sepolia RPC and dedicated test wallet.
5. Save the ABI to `artifacts/ContentVerifier.abi.json`.
6. Save the deployed address as the `CONTRACT_ADDRESS` Colab Secret.

The repository deliberately does not contain a private key or a real deployed address.
