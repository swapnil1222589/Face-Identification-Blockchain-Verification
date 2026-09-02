from __future__ import annotations

import tempfile
from pathlib import Path

from .face import FaceEngine, select_primary_face
from .hashing import content_fingerprint
from .matcher import MatchConfig, rank_candidates
from .search import search_web_for_image


class DemoState:
    def __init__(self):
        self.best = None
        self.content_hash = None
        self.tx_hash = None


def build_gradio_demo(engine, blockchain_client=None):
    """Build a small Colab-friendly Gradio interface.

    The blockchain client is optional so search/matching can be demonstrated
    independently when a testnet wallet is not configured.
    """
    import gradio as gr

    state = DemoState()

    def search_match(image, threshold):
        if image is None:
            return "Upload an image first.", None, None

        path = Path(tempfile.mkstemp(suffix=".jpg")[1])
        try:
            # Gradio normally supplies a filepath when type='filepath'.
            # Copying the bytes makes the function robust across Gradio versions.
            source = Path(image)
            path.write_bytes(source.read_bytes())

            _, faces = engine.detect_from_path(path)
            if not faces:
                return "✗ No face detected.", None, None

            target = select_primary_face(faces)
            candidates, _ = search_web_for_image(path, max_candidates=12)
            ranked = rank_candidates(
                engine,
                target.embedding,
                candidates,
                config=MatchConfig(threshold=float(threshold)),
            )
            matches = [c for c in ranked if c.status == "MATCH" and c.downloaded_image]
            if not matches:
                return (
                    f"Search completed, but no candidate reached threshold {float(threshold):.2f}.",
                    None,
                    None,
                )

            best = matches[0]
            state.best = best
            state.content_hash = content_fingerprint(
                image_bytes=best.downloaded_image,
                source_url=best.url,
                title=best.title,
                platform=best.platform or "",
                snippet=best.snippet or "",
            )

            rows = []
            for i, c in enumerate(ranked[:8], 1):
                score = "N/A" if c.face_similarity is None else f"{c.face_similarity*100:.1f}%"
                rows.append(
                    f"Candidate {i} | {c.platform} | similarity={score} | {c.status}\n{c.url}"
                )
            details = (
                f"Face detected: ✓ ({len(faces)})\n"
                f"Embedding generated: ✓\n"
                f"Best match: {best.platform} — {best.title}\n"
                f"URL: {best.url}\n"
                f"Similarity: {best.face_similarity*100:.1f}%\n"
                f"SHA-256: {state.content_hash}\n\n"
                "SEARCH RESULTS\n" + "\n\n".join(rows)
            )
            return details, state.content_hash, best.url
        except Exception as exc:
            return f"✗ Pipeline step failed: {type(exc).__name__}: {exc}", None, None
        finally:
            path.unlink(missing_ok=True)

    def register():
        if blockchain_client is None:
            return "✗ Blockchain client is not configured."
        if not state.best or not state.content_hash:
            return "Run SEARCH & MATCH first."
        try:
            state.tx_hash = blockchain_client.register(state.content_hash, state.best.url)
            return f"✓ REGISTERED\nTransaction: {state.tx_hash}"
        except Exception as exc:
            return f"✗ Registration failed: {type(exc).__name__}: {exc}"

    def verify():
        if blockchain_client is None:
            return "✗ Blockchain client is not configured."
        if not state.content_hash:
            return "Run SEARCH & MATCH first."
        try:
            result = blockchain_client.verify(state.content_hash)
            status = "✓ VERIFIED" if result["exists"] else "✗ NOT VERIFIED"
            return (
                f"{status}\n"
                f"Source: {result['source_url']}\n"
                f"Timestamp: {result['timestamp']}\n"
                f"Submitter: {result['submitter']}"
            )
        except Exception as exc:
            return f"✗ Verification failed: {type(exc).__name__}: {exc}"

    with gr.Blocks(title="HH Goa — FaceChain Verify") as demo:
        gr.Markdown(
            "# HH GOA — CONTENT VERIFICATION\n"
            "Face/content matching + genuine reverse-image search + SHA-256 + blockchain"
        )
        with gr.Row():
            image = gr.Image(type="filepath", label="Upload Face Image")
            threshold = gr.Slider(
                minimum=0.30, maximum=0.90, value=0.55, step=0.01,
                label="Face Similarity Threshold",
            )

        search_btn = gr.Button("SEARCH & MATCH", variant="primary")
        results = gr.Textbox(label="Search / Match Results", lines=18)
        hash_box = gr.Textbox(label="Content SHA-256")
        source_box = gr.Textbox(label="Selected Matching Post URL")

        with gr.Row():
            register_btn = gr.Button("REGISTER ON BLOCKCHAIN")
            verify_btn = gr.Button("VERIFY")

        tx_box = gr.Textbox(label="Blockchain Registration")
        verify_box = gr.Textbox(label="Blockchain Status")

        search_btn.click(
            search_match,
            inputs=[image, threshold],
            outputs=[results, hash_box, source_box],
        )
        register_btn.click(register, outputs=tx_box)
        verify_btn.click(verify, outputs=verify_box)

    return demo
