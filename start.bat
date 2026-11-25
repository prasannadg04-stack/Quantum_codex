@echo off
REM Runs the HeadCursor control panel from source (no .exe needed).
cd /d "%~dp0"
if not exist venv (
  python -m venv venv
  call venv\Scripts\activate
  pip install -r requirements.txt
) else (
  call venv\Scripts\activate
)
python app.py
pause
