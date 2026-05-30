"""Verify build_multipart and that signed multipart bodies round-trip."""

from __future__ import annotations

from bot.auth import internal as internal_auth
from bot.internal_client import build_multipart


def test_form_only_multipart_is_parseable():
    body, content_type = build_multipart({"a": "1", "b": "two"}, file=None)
    assert content_type.startswith("multipart/form-data; boundary=")
    text = body.decode("utf-8")
    assert 'name="a"' in text
    assert "1\r\n" in text
    assert 'name="b"' in text
    assert "two\r\n" in text
    # Closing boundary present.
    boundary = content_type.split("boundary=")[1]
    assert f"--{boundary}--\r\n" in text


def test_multipart_with_file_contains_bytes():
    file_bytes = bytes(range(256))
    body, _ = build_multipart(
        {"image_path": "x/y.jpg"},
        file=("file", "image.jpg", file_bytes, "image/jpeg"),
    )
    assert b'filename="image.jpg"' in body
    assert b"Content-Type: image/jpeg" in body
    assert file_bytes in body


def test_signed_multipart_round_trip():
    body, _ = build_multipart(
        {"telegram_user_id": "12345"},
        file=("file", "x.jpg", b"\x00\x01\x02hello\xff", "image/jpeg"),
    )
    header = internal_auth.sign("POST", "/internal/tasks/solve_image", body)
    internal_auth.verify(header, "POST", "/internal/tasks/solve_image", body)


def test_signed_multipart_tampering_caught():
    body, _ = build_multipart({"a": "1"}, file=None)
    header = internal_auth.sign("POST", "/internal/x", body)
    # Flip one byte of the body — signature must reject.
    tampered = bytearray(body)
    # Find a value byte and flip a bit safely.
    for i, b in enumerate(tampered):
        if b == ord("1"):
            tampered[i] = ord("2")
            break
    import pytest
    with pytest.raises(internal_auth.InternalAuthError):
        internal_auth.verify(header, "POST", "/internal/x", bytes(tampered))
