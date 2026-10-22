#!/usr/bin/env python3
"""Adjust opacity of the focused Zathura window, leaving other apps alone."""
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys


def hyprctl(*args):
    return subprocess.check_output(["hyprctl", *args], text=True).strip()


def main():
    action = sys.argv[1]
    if action not in ("up", "down", "reset"):
        raise ValueError("Choose up, down or reset")
    # Held keys can launch overlapping processes; read and write as one operation.
    lock = Path(os.environ["XDG_RUNTIME_DIR"]) / "zathura-opacity.lock"
    with lock.open("w") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        window = json.loads(hyprctl("-j", "activewindow"))
        if window.get("class") not in ("org.pwmt.zathura", "Zathura", "zathura"):
            return
        target = "address:" + window["address"]
        current = float(hyprctl("getprop", target, "opacity"))
        value = 1.0 if action == "reset" else current + (0.05 if action == "up" else -0.05)
        value = f"{max(0.30, min(1.0, value)):.2f}"
        for prop in ("opacity", "opacity_inactive", "opacity_fullscreen"):
            action = "hl.dsp.window.set_prop({prop=" + json.dumps(prop) + ",value=" + json.dumps(value) + ",window=" + json.dumps(target) + "})"
            result = hyprctl("dispatch", action)
            if result != "ok":
                raise RuntimeError(result)


if __name__ == "__main__":
    main()
