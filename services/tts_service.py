"""
services/tts_service.py  -  Text-to-Speech with Coqui TTS (optional).

If Coqui TTS is not installed, the web page uses the browser's own voice (speechSynthesis) instead.
"""
import os
import uuid

_tts = None


def is_available():
    try:
        import TTS  # noqa: F401
        return True
    except Exception:
        return False


def synthesize(text, out_dir, model_name):
    """Create a .wav file for the text and return its path."""
    global _tts
    try:
        from TTS.api import TTS
    except Exception as exc:
        raise RuntimeError("Coqui TTS is not installed. See the Beginner Guide, Part 9.") from exc
    if _tts is None:
        _tts = TTS(model_name)
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "reply_%s.wav" % uuid.uuid4().hex[:8])
    _tts.tts_to_file(text=text, file_path=path)
    return path
