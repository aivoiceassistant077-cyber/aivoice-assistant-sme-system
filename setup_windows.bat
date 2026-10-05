@echo off
echo ============================================
echo  Group 10 - Voice Business Assistant SETUP
echo ============================================
python --version
if errorlevel 1 (
  echo Python is not installed or not added to PATH. Please read PART 2 of the Beginner Guide.
  pause
  exit /b
)
python -m venv .venv
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
python seed_demo.py
echo.
echo SETUP FINISHED. Now double-click run_windows.bat
pause
