"""
config.py  -  All the settings of the project are kept in this one file.
A beginner can change the values here (for example the business name).
"""
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # Used by Flask to protect the login session. Change it before real use.
    SECRET_KEY = os.environ.get("SECRET_KEY", "group10-change-this-secret-key")

    # Where the SQLite database file is stored.
    DATABASE = os.environ.get("DATABASE", os.path.join(BASE_DIR, "instance", "assistant.db"))

    # Name shown at the top of every page.
    BUSINESS_NAME = os.environ.get("BUSINESS_NAME", "Group 10 Demo Shop")
    CURRENCY_WORD = "leones"      # spoken by the assistant
    CURRENCY_SYMBOL = "Le"        # shown in tables

    # Speech-to-text (OpenAI Whisper). "tiny" and "base" are small and fast.
    WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "base")

    # Text-to-speech (Coqui TTS) model name.
    TTS_MODEL = os.environ.get("TTS_MODEL", "tts_models/en/ljspeech/tacotron2-DDC")

    # Folder where temporary audio files are saved.
    AUDIO_DIR = os.path.join(BASE_DIR, "instance", "audio")

    MAX_CONTENT_LENGTH = 25 * 1024 * 1024  # 25 MB upload limit for audio
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_HTTPONLY = True
