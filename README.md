# Multilingual Voice-First AI Business Assistant for Low-Resource SMEs

**Group 10 - Diploma in Information Technology, IPAM, University of Sierra Leone**
Supervisor: Mr. Oluwatosin B. Ayorinde

A voice-first assistant that lets a small-business owner record sales, manage stock, register customers,
book appointments and read reports by **speaking or typing** in English or Krio (Mende and Temne lexicons are provided
as starter files to be completed with native speakers).

## Quick start (Windows, VS Code terminal)
```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python seed_demo.py        # optional: sample shop data
python app.py
```
Open http://127.0.0.1:5000 - login: `admin` / `admin123`

Run the tests: `pip install -r requirements-dev.txt` then `python -m pytest -v`

## Folder map
| Path | What it is |
|---|---|
| `app.py` | Starts the web server, all pages and API routes |
| `config.py` | Settings (business name, Whisper model, secret key) |
| `database.py`, `schema.sql` | SQLite database code and table design |
| `database/schema_mysql.sql` | The same design for MySQL Workbench |
| `nlp/parser.py`, `nlp/lexicons/*.json` | Language detection, intent detection, entity extraction |
| `services/business.py` | Real actions: sales, stock, customers, appointments, reports |
| `services/speech_service.py` | OpenAI Whisper speech-to-text (optional install) |
| `services/tts_service.py` | Coqui TTS text-to-speech (optional install) |
| `templates/`, `static/` | HTML, CSS and JavaScript pages |
| `tests/` | Pytest test cases |
| `android_app/` | Android Studio (Java) app that opens the assistant on a phone |
| `docs/` | Beginner guide and report documents |

Full step-by-step instructions are in `docs/GROUP10_Beginner_Guide.docx`.
