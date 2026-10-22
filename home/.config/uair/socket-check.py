#!/usr/bin/env python3
"""Remove only a stale uair socket owned by this user; preserve live timers."""
import os
from pathlib import Path
import stat
import subprocess
import sys

path = Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"))/"uair.sock"
cleanup = "--cleanup" in sys.argv
try:
    info = path.lstat()
except FileNotFoundError:
    sys.exit(0)
if not stat.S_ISSOCK(info.st_mode) or info.st_uid != os.getuid():
    sys.exit("Refusing to modify a non-socket or a socket owned by another user")
try:
    result = subprocess.run(["/usr/bin/uairctl", "-s", str(path), "fetch", "{time}"],
                            capture_output=True, text=True, timeout=2)
except subprocess.TimeoutExpired:
    sys.exit("Existing uair socket did not respond; leaving it untouched")
if result.returncode == 0:
    # ExecCondition exit 1 skips starting another timer. Cleanup also leaves it alone.
    sys.exit(0 if cleanup else 1)
if "code: 111" not in result.stderr and "Connection refused" not in result.stderr:
    sys.exit("Cannot confirm that the existing uair socket is stale")
try:
    current = path.lstat()
    if (current.st_dev, current.st_ino) != (info.st_dev, info.st_ino):
        sys.exit("Socket changed during the check; leaving it untouched")
    path.unlink()
except FileNotFoundError:
    pass
