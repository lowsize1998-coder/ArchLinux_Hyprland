#!/usr/bin/env python3
"""Count foreground Zathura reading and send quiet break reminders."""
import json
from pathlib import Path
import subprocess
import time

SETTINGS = Path(__file__).with_name("settings.json")
CLASSES = {"org.pwmt.zathura", "Zathura", "zathura"}


class ReadingTimer:
    def __init__(self):
        self.elapsed = 0.0
        self.previous = None
        self.away_since = None

    def tick(self, now, reading, interval, rest):
        delta = max(0,now-self.previous) if self.previous is not None else 0
        self.previous = now
        if delta > 30 or interval == 0:
            self.elapsed = 0
            self.away_since = None
            return False
        if not reading:
            if self.away_since is None: self.away_since = now
            if now-self.away_since >= rest: self.elapsed = 0
            return False
        if self.away_since is not None:
            if now-self.away_since >= rest: self.elapsed = 0
            self.away_since = None
            delta = 0
        self.elapsed += delta
        if self.elapsed >= interval:
            self.elapsed = 0
            return True
        return False


def reading_window():
    result = subprocess.run(["hyprctl","-j","activewindow"],capture_output=True,text=True,timeout=3)
    if result.returncode: return False
    window = json.loads(result.stdout)
    if window.get("class") not in CLASSES: return False
    # Empty Zathura windows have no document and must not count as reading.
    title = window.get("title", "").strip()
    return bool(title and title.lower() not in {"zathura", "org.pwmt.zathura"})


def main():
    timer = ReadingTimer()
    while True:
        try:
            settings = json.loads(SETTINGS.read_text())
            minutes = float(settings["breakMinutes"])
            seconds = int(settings["breakSeconds"])
            if not 0 <= minutes <= 180 or not 1 <= seconds <= 300:
                raise ValueError("Invalid break duration")
            active = reading_window()
            if timer.tick(time.monotonic(),active,minutes*60,seconds):
                subprocess.run(["notify-send","--app-name=Zathura","--urgency=normal",
                    "--hint=boolean:suppress-sound:true",
                    "--expire-time=20000","Перерыв от чтения",
                    f"Посмотрите вдаль примерно на 6 метров в течение {seconds} секунд. Поморгайте и расслабьте глаза."],
                    timeout=5,check=False)
        except (OSError,ValueError,KeyError,subprocess.SubprocessError):
            timer.elapsed = 0
        time.sleep(5)


if __name__ == "__main__":
    main()
