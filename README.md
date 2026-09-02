# FaceChain Verify — Face Identification & Blockchain Content Verification

> HH Goa 2026 — Task 3 prototype, optimized for Google Colab.

## Problem

The challenge is to take a user-supplied face image, perform a genuine reverse-image/web search, identify a candidate result whose available image contains a similar face, fingerprint the discovered content, and register that fingerprint on an EVM-compatible blockchain for later verification.

**Important:** face matching is a face/content matching signal. It does **not** prove a person's real-world identity.

## Solution

```text
Uploaded Face
     │
     ▼
Face Detection + Embedding
     │
     ▼
Genuine Google Lens Search (SerpApi)
     │
     ▼
Candidate Images
     │
     ▼
Face Similarity Ranking
     │
     ▼
Best Valid Match
     │
     ▼
Canonical Content Record
     │
     ▼
SHA-256 Fingerprint
     │
     ▼
EVM Smart Contract
     │
     ▼
On-chain Verification
```

## Features

- InsightFace face detection and embeddings
- Genuine Google Lens reverse-image search through SerpApi
- Candidate image retrieval and face similarity ranking
- Configurable face-match threshold
- Deterministic SHA-256 content fingerprint
- Solidity registry contract
- `web3.py` registration and verification
- Colab/Gradio demo UI with SEARCH & MATCH, REGISTER, and VERIFY controls
- Unit tests for hashing, matching logic, and blockchain configuration

## Architecture

```mermaid
flowchart LR
    A[Upload Face Image] --> B[InsightFace]
    B --> C[Face Embedding]
    C --> D[SerpApi Google Lens]
    D --> E[Candidate URLs / Images]
    E --> F[Candidate Face Embeddings]
    F --> G[Cosine Similarity]
    G --> H[Best Match]
    H --> I[Canonical Content Record]
    I --> J[SHA-256]
    J --> K[ContentVerifier.sol]
    K --> L[Sepolia / EVM Testnet]
    L --> M[Read + Verify]
```

## Tech stack

- Python 3
- InsightFace + ONNX Runtime
- OpenCV
- SerpApi Google Lens
- Gradio
- Solidity `^0.8.24`
- `web3.py`
- Ethereum Sepolia (recommended demo network)

## Google Colab setup

1. Open `HH_Goa_Task3.ipynb` in Google Colab.
2. Run the dependency installation cell.
3. Add the following secrets through **Colab → Secrets**:
   - `SERPAPI_KEY`
   - `RPC_URL`
   - `PRIVATE_KEY`
   - `CONTRACT_ADDRESS`
4. Enable notebook access to each secret.
5. Run the face-processing setup.
6. Run the search/matching section.
7. Run the blockchain section.
8. Upload a face image and execute the demo.

The SerpApi adapter uploads the local image first and then uses the temporary image ID for Google Lens. SerpApi documents a 500 KB upload limit and a temporary image ID lifetime, so the notebook compresses large inputs before upload.

## API configuration

### SerpApi

`SERPAPI_KEY` is required for genuine reverse-image search.

The implementation uses Google Lens rather than a hardcoded URL. The search layer records the returned title, URL, domain/platform, image URL, and snippet where available.

SerpApi availability and social-platform indexing can vary. A search result is not guaranteed for every image, and private/login-only social content may not be accessible.

### Blockchain

Recommended demo network: Ethereum Sepolia.

Required secrets:

- `RPC_URL` — an HTTPS RPC endpoint for Sepolia
- `PRIVATE_KEY` — a dedicated test wallet key; never use a valuable wallet
- `CONTRACT_ADDRESS` — deployed `ContentVerifier` contract

The notebook can compile and deploy the contract if desired. For a repeatable demo, deploy once and save the contract address in `CONTRACT_ADDRESS`.

Do not commit any private key, API key, or funded-wallet secret.

## Contract behavior

`registerContent(bytes32 contentHash, string sourceUrl)` stores:

- content hash
- source/reference URL
- block timestamp
- submitting address

It emits `ContentRegistered`.

`verifyContent(bytes32 contentHash)` returns whether a record exists.

`getRecord(bytes32 contentHash)` returns the stored source URL, timestamp, and submitter.

## What exactly is hashed?

The fingerprint is SHA-256 over a canonical UTF-8 JSON record with sorted keys and compact separators:

```json
{
  "image_sha256": "<SHA-256 of downloaded discovered image bytes>",
  "platform": "<platform/domain>",
  "snippet": "<search snippet if available>",
  "source_url": "<discovered result URL>",
  "title": "<discovered result title>"
}
```

The API key, private key, and other secrets are never included.

Because the downloaded image bytes are included indirectly through `image_sha256`, a changed image produces a different fingerprint. Metadata changes also change the fingerprint.

## Matching threshold

The face similarity threshold is configurable in the notebook and in `app/matcher.py`.

The default example is `0.55` cosine similarity, but it should be tuned using the actual demo data. **Do not present the threshold as a universal identity boundary.**

The UI displays the configured threshold so judges can see that it is an explicit parameter.

## Error handling

The prototype does not fake successful results. It reports failures for:

- no face detected
- invalid/multiple face input
- no search results
- candidate image unavailable
- candidate image contains no face
- low similarity
- API errors/rate limits
- invalid/missing RPC
- failed blockchain transactions
- insufficient testnet funds
- missing credentials

## Testing

Run:

```bash
pytest -q
```

Blockchain unit tests use configuration/error checks and can be extended with a mocked contract client. The live Colab demo is the path that performs a real on-chain transaction.

Do not describe mocked blockchain tests as live blockchain verification.

## Demo checklist

A judge should be able to see:

```text
Uploaded image
      ↓
Face detected + embedding
      ↓
Actual Google Lens search request
      ↓
Actual candidate result
      ↓
Actual candidate face comparison
      ↓
Actual SHA-256 fingerprint
      ↓
Actual blockchain transaction
      ↓
Actual blockchain read-back
      ↓
VERIFIED
```

The notebook prints the search engine, candidate URL, similarity, hash, transaction hash, and verification record so the pipeline is auditable.

## Limitations

- Reverse-image search depends on the external search provider and its index.
- Social media sites can restrict crawling/indexing or require login.
- Candidate image URLs can expire or reject automated downloads.
- Face recognition can produce false positives and false negatives.
- Different poses, occlusion, lighting, crops, and image quality can reduce similarity.
- A face similarity score is not proof of identity.
- Blockchain transactions require testnet ETH and can take time.
- A blockchain record proves that a specific fingerprint/reference was registered; it does not independently prove that the online post is authentic or that the person is who the post claims.

## License

MIT.
