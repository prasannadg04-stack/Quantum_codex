"""
HeadCursor engine - head-tracking cursor with dwell click and eyes-closed backspace.
Built on our earlier HeadStart prototype (MediaPipe Tasks API, Python 3.11 - 3.13).

Two ways to use it:
  1. Control panel app (for students):   python app.py        (big buttons, no keyboard needed)
  2. Developer mode with a camera window: python head_cursor.py
     keys: c calibrate | r reset | b eye backspace | [ ] sensitivity | q quit
"""

import os
import shutil
import sys
import threading
import time
import urllib.request

import cv2
import numpy as np
import pyautogui
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

pyautogui.FAILSAFE = False   # a head-mouse user could hit a screen corner by accident
pyautogui.PAUSE = 0

SCREEN_W, SCREEN_H = pyautogui.size()

MODEL_NAME = "face_landmarker.task"
MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "face_landmarker/face_landmarker/float16/1/face_landmarker.task"
)


def resource_dir():
    """Folder holding bundled files (works both from source and inside the .exe)."""
    return getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))


def user_data_dir():
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    path = os.path.join(base, "HeadCursor")
    os.makedirs(path, exist_ok=True)
    return path


def ensure_model():
    """Return the model path: bundled copy first, else download once."""
    bundled = os.path.join(resource_dir(), MODEL_NAME)
    if os.path.exists(bundled):
        return bundled
    local = os.path.join(user_data_dir(), MODEL_NAME)
    if not os.path.exists(local):
        print("First run: downloading the face-tracking model (needs internet, one time only)...")
        urllib.request.urlretrieve(MODEL_URL, local)
    return local


NOSE_TIP = 1  # tracked point; nudge to 4 if it feels off on your face/camera
L_EYE = [33, 160, 158, 133, 153, 144]
R_EYE = [362, 385, 387, 263, 373, 380]


def eye_openness(pts, idx):
    p = [np.array([pts[i].x, pts[i].y]) for i in idx]
    vertical = np.linalg.norm(p[1] - p[5]) + np.linalg.norm(p[2] - p[4])
    horizontal = 2.0 * np.linalg.norm(p[0] - p[3])
    return vertical / horizontal if horizontal else 1.0


class HeadCursor:
    # ---- tuning ----
    ALPHA = 0.25          # smoothing: lower = smoother but slower
    RANGE_X = 0.08        # nose movement (0-1 camera units) to cross the screen
    RANGE_Y = 0.06
    DEAD_ZONE = 6         # pixels: tiny shakes are ignored
    DWELL_TIME = 1.0      # seconds holding still before a click
    DWELL_RADIUS = 40     # pixels of wobble allowed while holding
    EAR_CLOSED = 0.19     # eye openness below this = closed (raise if backspace never triggers)
    CLOSE_HOLD = 0.8      # seconds eyes must stay closed for Backspace
    REPEAT_EVERY = 0.5    # seconds between repeated Backspaces

    def __init__(self, show_window=False):
        self.show_window = show_window
        self.sensitivity = 1.0
        self.backspace_on = True
        self.calib_center = None
        self.status = "Starting..."
        self.openness = 1.0
        self.error = None
        self.running = False
        self._calib_at = None
        self._smooth = [SCREEN_W / 2, SCREEN_H / 2]
        self._dwell_anchor = None
        self._dwell_start = 0.0
        self._click_locked = False
        self._closed_since = None
        self._last_backspace = 0.0
        self._thread = None
        self._landmarker = None

    # ---- controls (called by buttons or keys) ----
    def start_calibration(self, seconds=3.0):
        """Capture the centre position after a countdown, so the user can move off the button first."""
        self._calib_at = time.time() + seconds

    def reset_calibration(self):
        self.calib_center = None
        self._calib_at = None

    def toggle_backspace(self):
        self.backspace_on = not self.backspace_on
        self._closed_since = None
        return self.backspace_on

    def change_sensitivity(self, delta):
        self.sensitivity = round(max(0.4, min(3.0, self.sensitivity + delta)), 1)
        return self.sensitivity

    # ---- running ----
    def start(self):
        self.running = True
        self._thread = threading.Thread(target=self.run, daemon=True)
        self._thread.start()

    def stop(self):
        self.running = False

    def _make_landmarker(self):
        options = vision.FaceLandmarkerOptions(
            base_options=mp_python.BaseOptions(model_asset_path=ensure_model()),
            running_mode=vision.RunningMode.IMAGE,
            num_faces=1,
        )
        return vision.FaceLandmarker.create_from_options(options)

    def _detect(self, frame_bgr):
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        result = self._landmarker.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb))
        if not result.face_landmarks:
            return None
        pts = result.face_landmarks[0]
        nose = pts[NOSE_TIP]
        openness = (eye_openness(pts, L_EYE) + eye_openness(pts, R_EYE)) / 2
        return nose.x, nose.y, openness

    def run(self):
        try:
            self._landmarker = self._make_landmarker()
        except Exception as e:  # no internet on first run, etc.
            self.error = f"Could not load the face model: {e}"
            self.status = self.error
            return

        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            self.error = "Could not open the webcam. Close other apps using it and try again."
            self.status = self.error
            return

        while self.running:
            ok, frame = cap.read()
            if not ok:
                break
            frame = cv2.flip(frame, 1)
            face = self._detect(frame)
            self._step(face)

            if self.show_window:
                cv2.putText(frame, self.status, (16, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 230, 0), 2)
                cv2.putText(frame, f"Eye backspace {'ON' if self.backspace_on else 'OFF'}  sens x{self.sensitivity:.1f}"
                                   f"  eye openness {self.openness:.2f}",
                            (16, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
                cv2.putText(frame, "c: calibrate  r: reset  b: eye backspace  [ ]: sensitivity  q: quit",
                            (16, frame.shape[0] - 16), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)
                cv2.imshow("HeadCursor", frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    self.running = False
                elif key == ord('c'):
                    self.start_calibration(0)
                elif key == ord('r'):
                    self.reset_calibration()
                elif key == ord('b'):
                    self.toggle_backspace()
                elif key == ord('['):
                    self.change_sensitivity(-0.1)
                elif key == ord(']'):
                    self.change_sensitivity(0.1)

        cap.release()
        if self.show_window:
            cv2.destroyAllWindows()
        self.running = False

    def _step(self, face):
        if face is None:
            self.status = "No face found - sit in front of the camera"
            return
        nx, ny, self.openness = face
        now = time.time()

        # calibration with countdown
        if self._calib_at is not None:
            remaining = self._calib_at - now
            if remaining > 0:
                self.status = f"Look at the CENTER of the screen... {remaining:.0f}"
                return
            self.calib_center = (nx, ny)
            self._calib_at = None
            self._dwell_anchor = None

        if self.calib_center is None:
            self.status = "Not calibrated - click Calibrate"
            return

        # eyes closed -> backspace (cursor stays frozen)
        if self.backspace_on and self.openness < self.EAR_CLOSED:
            if self._closed_since is None:
                self._closed_since = now
            held = now - self._closed_since
            self._dwell_anchor = None
            if held >= self.CLOSE_HOLD and now - self._last_backspace >= self.REPEAT_EVERY:
                pyautogui.press('backspace')
                self._last_backspace = now
                self.status = "BACKSPACE"
            else:
                self.status = f"Eyes closed... {min(held, self.CLOSE_HOLD):.1f}s / {self.CLOSE_HOLD:.1f}s"
            return
        self._closed_since = None

        # head -> cursor
        cx, cy = self.calib_center
        dx = max(-1.0, min(1.0, (nx - cx) / (self.RANGE_X / self.sensitivity)))
        dy = max(-1.0, min(1.0, (ny - cy) / (self.RANGE_Y / self.sensitivity)))
        target_x = SCREEN_W / 2 + dx * (SCREEN_W / 2 - 10)
        target_y = SCREEN_H / 2 + dy * (SCREEN_H / 2 - 10)

        sx, sy = self._smooth
        if abs(target_x - sx) > self.DEAD_ZONE or abs(target_y - sy) > self.DEAD_ZONE:
            sx = self.ALPHA * target_x + (1 - self.ALPHA) * sx
            sy = self.ALPHA * target_y + (1 - self.ALPHA) * sy
            self._smooth = [sx, sy]
        pyautogui.moveTo(sx, sy)

        # dwell click
        anchor = self._dwell_anchor
        if anchor is None or abs(sx - anchor[0]) > self.DWELL_RADIUS or abs(sy - anchor[1]) > self.DWELL_RADIUS:
            self._dwell_anchor = (sx, sy)
            self._dwell_start = now
            self._click_locked = False
            self.status = "Tracking"
        else:
            elapsed = now - self._dwell_start
            if elapsed >= self.DWELL_TIME and not self._click_locked:
                pyautogui.click()
                self._click_locked = True
                self.status = "CLICK!"
            elif not self._click_locked:
                self.status = f"Holding... {elapsed:.1f}s / {self.DWELL_TIME:.1f}s"
            else:
                self.status = "Move to reset"


def main():
    tracker = HeadCursor(show_window=True)
    print("Look at the CENTER of your screen, then press 'c' to calibrate. Press 'q' to quit.")
    tracker.run()


if __name__ == "__main__":
    main()
