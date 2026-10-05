"""
services/speech_service.py  -  Speech-to-Text with OpenAI Whisper (optional).

Whisper is a big library, so it is OPTIONAL. If it is not installed the assistant still works:
the browser (Chrome) can listen to the microphone, or the user can type.
Install Whisper later with:   pip install -r requirements-voice.txt
"""
_model = None


def is_available():
    try:
        import whisper  # noqa: F401
        return True
    except Exception:
        return False


def transcribe(path, model_name="base", language=None):
    """Convert an audio file into text. language: 'en' or None (auto-detect)."""
    global _model
    try:
        import whisper
    except Exception as exc:
        raise RuntimeError("Whisper is not installed. See the Beginner Guide, Part 9.") from exc
    if _model is None:
        _model = whisper.load_model(model_name)
    result = _model.transcribe(path, language=language, fp16=False)
    return (result.get("text") or "").strip()
