@echo off
REM Builds HeadCursor.exe (a normal Windows program) - run this once on a Windows laptop.
cd /d "%~dp0"

if not exist venv (
  python -m venv venv
)
call venv\Scripts\activate
pip install -r requirements.txt
pip install pyinstaller

if not exist face_landmarker.task (
  echo Downloading face model for bundling...
  curl -L -o face_landmarker.task https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task
)

if not exist vosk-model-small-en-in-0.4 (
  echo Downloading voice model for bundling...
  curl -L -o vosk-model.zip https://alphacephei.com/vosk/models/vosk-model-small-en-in-0.4.zip
  powershell -Command "Expand-Archive -Force vosk-model.zip ."
  del vosk-model.zip
)

pyinstaller --noconfirm --windowed --name HeadCursor ^
  --collect-all mediapipe ^
  --collect-all vosk ^
  --hidden-import sounddevice ^
  --add-data "face_landmarker.task;." ^
  --add-data "vosk-model-small-en-in-0.4;vosk-model-small-en-in-0.4" ^
  app.py

echo.
echo Done. The program is in dist\HeadCursor\HeadCursor.exe
echo To make an installer for NGO computers, open installer.iss in Inno Setup and press Compile.
pause
