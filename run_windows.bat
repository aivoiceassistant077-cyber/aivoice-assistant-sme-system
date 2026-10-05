@echo off
call .venv\Scripts\activate
echo Starting the assistant... open http://127.0.0.1:5000 in Chrome
python app.py
pause
