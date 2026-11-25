"""
Voice commands for HeadCursor - like "Voice Access" on phones, but for the PC.

Works OFFLINE with Vosk. It only listens for a fixed list of commands (listed in
COMMANDS below), which makes it far more accurate than free dictation.
The first run downloads a small English (India) speech model (~40 MB, one time).
"""

import json
import os
import queue
import subprocess
import threading
import urllib.request
import zipfile

import pyautogui

from head_cursor import resource_dir, user_data_dir

MODEL_DIR_NAME = "vosk-model-small-en-in-0.4"
MODEL_URL = f"https://alphacephei.com/vosk/models/{MODEL_DIR_NAME}.zip"

APPS = {
    "whatsapp": "whatsapp:",
    "chrome": "chrome",
    "browser": "msedge",
    "notepad": "notepad",
    "calculator": "calc",
    "camera": "microsoft.windows.camera:",
}


def _press(*keys):
    return lambda: pyautogui.hotkey(*keys) if len(keys) > 1 else pyautogui.press(keys[0])


def _open_app(target):
    return lambda: subprocess.Popen(f'start "" "{target}"', shell=True)


# spoken phrase -> action
COMMANDS = {
    "backspace": _press("backspace"),
    "delete": _press("delete"),
    "enter": _press("enter"),
    "space": _press("space"),
    "tab": _press("tab"),
    "escape": _press("esc"),
    "click": lambda: pyautogui.click(),
    "double click": lambda: pyautogui.doubleClick(),
    "right click": lambda: pyautogui.rightClick(),
    "scroll up": lambda: pyautogui.scroll(600),
    "scroll down": lambda: pyautogui.scroll(-600),
    "go back": _press("alt", "left"),
    "select all": _press("ctrl", "a"),
    "copy": _press("ctrl", "c"),
    "paste": _press("ctrl", "v"),
    "undo": _press("ctrl", "z"),
    "close window": _press("alt", "f4"),
    "show desktop": _press("win", "d"),
}
for _name, _target in APPS.items():
    COMMANDS[f"open {_name}"] = _open_app(_target)

SLEEP_PHRASE = "stop listening"
WAKE_PHRASE = "start listening"


def ensure_voice_model():
    """Return the model folder: bundled copy first, else download once."""
    bundled = os.path.join(resource_dir(), MODEL_DIR_NAME)
    if os.path.isdir(bundled):
        return bundled
    local = os.path.join(user_data_dir(), MODEL_DIR_NAME)
    if not os.path.isdir(local):
        zip_path = local + ".zip"
        urllib.request.urlretrieve(MODEL_URL, zip_path)
        with zipfile.ZipFile(zip_path) as z:
            z.extractall(user_data_dir())
        os.remove(zip_path)
    return local


class VoiceCommands:
    def __init__(self):
        self.enabled = True      # turned on/off by the panel button
        self.asleep = False      # "stop listening" / "start listening"
        self.status = "Voice: starting..."
        self.last_heard = ""
        self.error = None
        self.running = False
        self._thread = None

    def start(self):
        self.running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self.running = False

    def toggle(self):
        self.enabled = not self.enabled
        self.status = "Voice: ON - say a command" if self.enabled else "Voice: OFF"
        return self.enabled

    def _run(self):
        try:
            import sounddevice as sd
            from vosk import KaldiRecognizer, Model, SetLogLevel

            SetLogLevel(-1)
            self.status = "Voice: loading speech model (first run downloads ~40 MB)..."
            model = Model(ensure_voice_model())
            grammar = list(COMMANDS) + [SLEEP_PHRASE, WAKE_PHRASE, "[unk]"]
            recognizer = KaldiRecognizer(model, 16000, json.dumps(grammar))
            audio = queue.Queue()

            def on_audio(indata, frames, time_info, status):
                audio.put(bytes(indata))

            with sd.RawInputStream(samplerate=16000, blocksize=4000, dtype="int16",
                                   channels=1, callback=on_audio):
                self.status = "Voice: ON - say a command"
                while self.running:
                    data = audio.get()
                    if not self.enabled:
                        continue
                    if recognizer.AcceptWaveform(data):
                        text = json.loads(recognizer.Result()).get("text", "").strip()
                        if text and text != "[unk]":
                            self._handle(text)
        except Exception as e:
            self.error = f"Voice unavailable: {e}"
            self.status = self.error

    def _handle(self, text):
        self.last_heard = text
        if text == WAKE_PHRASE:
            self.asleep = False
            self.status = "Voice: awake - say a command"
        elif text == SLEEP_PHRASE:
            self.asleep = True
            self.status = 'Voice: asleep - say "start listening"'
        elif self.asleep:
            return
        elif text in COMMANDS:
            COMMANDS[text]()
            self.status = f'Voice: did "{text}"'
