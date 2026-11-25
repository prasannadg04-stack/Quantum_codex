# HeadCursor (Team Quantum Codex)

Control your computer cursor with your head, using only a webcam, and give voice commands.
Built on our earlier HeadStart prototype and extended for COMPUTE50.

A student with no use of their hands can run everything without a keyboard:
the cursor follows the head, holding still for 1 second clicks, and all controls are
big on-screen buttons that the head cursor can click.

## Features
- Head-tracking cursor with smoothing, dead zone and adjustable speed
- Dwell click (hold still ~1 second)
- Eyes-closed Backspace (close both eyes ~0.8 s; keep closed to repeat)
- Offline voice commands (Vosk): backspace, enter, click, scroll up/down, copy, paste, open whatsapp / chrome ...
  Say "stop listening" / "start listening" to pause and resume
- Control panel with big buttons: Calibrate (3 s countdown), Reset, Eye Backspace, Voice, Slower / Faster, Quit

## How to run (Windows)
1. Install Python 3.11, 3.12 or 3.13 and tick "Add Python to PATH".
2. Double-click `start.bat`. The first run installs libraries and downloads the face and voice models (needs internet once).
3. In the panel click **Calibrate**, then look at the CENTRE of the screen until the countdown ends.
4. Move your head to move the cursor. Hold still on a button for 1 second to click it.

Developer mode with a camera window and keys (c, r, b, [ ], q): `python head_cursor.py`

## Build the Windows program / installer (untested)
1. Run `build_exe.bat` -> `dist\HeadCursor\HeadCursor.exe`
2. Open `installer.iss` in Inno Setup and Compile -> `HeadCursor-Setup.exe` for NGO computers

## Tuning
See the settings at the top of `HeadCursor` in `head_cursor.py`
(`EAR_CLOSED`, `CLOSE_HOLD`, `DWELL_TIME`, `RANGE_X`, `RANGE_Y`).

Status: prototype. Not yet tested on real users.
