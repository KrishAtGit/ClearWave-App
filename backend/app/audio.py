from typing import NamedTuple

class AudioType(NamedTuple):
    extension: str
    content_type: str

def detect_audio(data: bytes) -> AudioType | None:
    # identifies an audio file by its first bytes (its "magic number"), not by its name or the type the browser
    # claims, both of which anyone can fake. Returns None for anything that isn't a supported audio format.
    head = data[:12]
    if head[:4] == b"RIFF" and head[8:12] == b"WAVE":
        return AudioType("wav", "audio/wav")
    if head[:4] == b"FORM" and head[8:12] in [b"AIFF", b"AIFC"]:
        return AudioType("aiff", "audio/aiff")
    if head[:4] == b"fLaC":
        return AudioType("flac", "audio/flac")
    if head[:4] == b"OggS":
        return AudioType("ogg", "audio/ogg")
    if head[4:8] == b"ftyp":
        return AudioType("m4a", "audio/mp4")
    if head[:3] == b"ID3" or (len(head) >= 2 and head[0] == 0xFF and head[1] & 0xE0 == 0xE0):
        return AudioType("mp3", "audio/mpeg")
    return None
