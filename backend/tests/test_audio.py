from app.audio import detect_audio


def test_detects_common_audio_formats() -> None:
    assert detect_audio(b"RIFF\x00\x00\x00\x00WAVEfmt ").extension == "wav"  # type: ignore[union-attr]
    assert detect_audio(b"ID3\x04\x00\x00\x00\x00\x00\x00\x00\x00").extension == "mp3"  # type: ignore[union-attr]
    assert detect_audio(b"\xff\xfb\x90\x00" + b"\x00" * 8).extension == "mp3"  # type: ignore[union-attr]
    assert detect_audio(b"fLaC\x00\x00\x00\x22" + b"\x00" * 4).extension == "flac"  # type: ignore[union-attr]
    assert detect_audio(b"OggS\x00\x02" + b"\x00" * 6).extension == "ogg"  # type: ignore[union-attr]
    assert detect_audio(b"\x00\x00\x00\x20ftypM4A ").extension == "m4a"  # type: ignore[union-attr]
    assert detect_audio(b"FORM\x00\x00\x00\x00AIFF").extension == "aiff"  # type: ignore[union-attr]


def test_rejects_everything_else() -> None:
    assert detect_audio(b"%PDF-1.7 not audio") is None
    assert detect_audio(b"\x89PNG\r\n\x1a\n....") is None
    assert detect_audio(b"") is None