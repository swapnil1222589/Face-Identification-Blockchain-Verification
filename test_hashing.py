import hashlib

from app.hashing import canonical_content_record, content_fingerprint


def test_identical_content_has_identical_hash():
    kwargs = dict(
        image_bytes=b"image",
        source_url="https://example.com/post/1",
        title="Example",
        platform="Example",
        snippet="hello",
    )
    assert content_fingerprint(**kwargs) == content_fingerprint(**kwargs)


def test_modified_content_changes_hash():
    base = dict(
        image_bytes=b"image",
        source_url="https://example.com/post/1",
        title="Example",
        platform="Example",
        snippet="hello",
    )
    changed = {**base, "image_bytes": b"modified-image"}
    assert content_fingerprint(**base) != content_fingerprint(**changed)


def test_canonical_record_is_deterministic():
    payload = canonical_content_record(
        image_bytes=b"x",
        source_url="https://example.com",
    )
    expected_image_hash = hashlib.sha256(b"x").hexdigest()
    assert expected_image_hash.encode() in payload
