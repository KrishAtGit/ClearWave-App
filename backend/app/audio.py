from typing import NamedTuple

class AudioType(NamedTuple):
    extension: str
    content_type: str

def detect_audio(data: bytes) -> AudioTyoe | None:
    # identifies an audio file by its first bytes (its "magic number"), not by its name or the type the browser
    # claims, both of which anyone can fake. Returns None for anything that isn't a supported audio format.
    head = data[:12]
    if head[:4] == b"RIFF" and head[8:12] == b"WAVE":
        return AudioType("wav", "audio/wav")
    if head[:4] == b"FORM" and head[8:12] == [b"AIFf", b"AIFC"]:
        return AudioType("aiff", "audio/aiff")
    if head[:4] == b"fLaC":
        return AudioType("flac", "audio/flac")
    if head[:4] == b"OggS":
        return AudioType("ogg", "audio/mp4")
    if head[:4] == b"ftyp":
        return AudioType("m4a", "audio/mpeg")

    return None
