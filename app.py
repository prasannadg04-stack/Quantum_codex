"""
HeadCursor control panel - the app students and NGOs actually run.

A small always-on-top panel with BIG buttons. Because the head cursor clicks by
dwell (hold still ~1 second), every button here can be used with only head
movement - no keyboard or mouse needed.
"""

import tkinter as tk

from head_cursor import HeadCursor
from voice import VoiceCommands

BG = "#06122a"
PANEL = "#12264a"
CYAN = "#22d3ee"
TEXT = "#e6fbff"
RED = "#ef4444"

WIDTH = 300
BTN = dict(font=("Segoe UI", 18, "bold"), bd=0, relief="flat", height=2, cursor="hand2")


class Panel:
    def __init__(self):
        self.tracker = HeadCursor()
        self.voice = VoiceCommands()
        self.root = tk.Tk()
        self.root.title("HeadCursor")
        self.root.configure(bg=BG)
        self.root.attributes("-topmost", True)
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.quit)
        # dock on the right edge of the screen
        self.root.geometry(f"{WIDTH}x780+{self.root.winfo_screenwidth() - WIDTH - 8}+40")

        tk.Label(self.root, text="HeadCursor", font=("Segoe UI", 20, "bold"), fg=CYAN, bg=BG).pack(pady=(12, 0))
        self.status = tk.Label(self.root, text="Starting...", font=("Segoe UI", 12), fg=TEXT, bg=BG,
                               wraplength=WIDTH - 24, justify="center", height=3)
        self.status.pack(padx=12)

        self._button("Calibrate", lambda: self.tracker.start_calibration(3.0), CYAN, BG)
        self._button("Reset", self.tracker.reset_calibration, PANEL, TEXT)
        self.bs_btn = self._button("", self.toggle_backspace, PANEL, TEXT)
        self.voice_btn = self._button("", self.toggle_voice, PANEL, TEXT)
        self.voice_status = tk.Label(self.root, text="", font=("Segoe UI", 11), fg=CYAN, bg=BG,
                                     wraplength=WIDTH - 24, justify="center", height=2)
        self.voice_status.pack(padx=12)
        self.sens_label = tk.Label(self.root, font=("Segoe UI", 12), fg=TEXT, bg=BG)
        self.sens_label.pack(pady=(8, 0))
        row = tk.Frame(self.root, bg=BG)
        row.pack(fill="x", padx=12, pady=4)
        for text, delta in (("Slower", -0.2), ("Faster", 0.2)):
            tk.Button(row, text=text, command=lambda d=delta: self.change_sens(d),
                      bg=PANEL, fg=TEXT, activebackground=CYAN, width=8, **BTN).pack(
                side="left", expand=True, fill="x", padx=3)
        tk.Frame(self.root, bg=BG, height=16).pack()
        self._button("Quit", self.quit, RED, "white")

        self.refresh_labels()
        self.tracker.start()
        self.voice.start()
        self.poll()

    def _button(self, text, command, bg, fg):
        b = tk.Button(self.root, text=text, command=command, bg=bg, fg=fg, activebackground=CYAN, **BTN)
        b.pack(fill="x", padx=12, pady=4)
        return b

    def toggle_backspace(self):
        self.tracker.toggle_backspace()
        self.refresh_labels()

    def toggle_voice(self):
        self.voice.toggle()
        self.refresh_labels()

    def change_sens(self, delta):
        self.tracker.change_sensitivity(delta)
        self.refresh_labels()

    def refresh_labels(self):
        on = self.tracker.backspace_on
        self.bs_btn.config(text=f"Eye Backspace: {'ON' if on else 'OFF'}")
        self.sens_label.config(text=f"Cursor speed: x{self.tracker.sensitivity:.1f}")
        self.voice_btn.config(text=f"Voice: {'ON' if self.voice.enabled else 'OFF'}")

    def poll(self):
        self.status.config(text=self.tracker.status)
        self.voice_status.config(text=self.voice.status)
        if not self.tracker.running and self.tracker.error is None and self.tracker._thread is not None \
                and not self.tracker._thread.is_alive():
            self.status.config(text="Camera stopped.")
        self.root.after(100, self.poll)

    def quit(self):
        self.tracker.stop()
        self.voice.stop()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    Panel().run()
