#!/usr/bin/env python3
"""Restore only preferences and CSS managed by Symphony Zen, preserving browser data."""
import argparse
import configparser
import datetime
import json
import os
import re
import shutil
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validate without changing files")
    parser.add_argument("--profile", type=Path, help="explicit profile path if more than one installation exists")
    args = parser.parse_args()
    home = Path.home()
    source = Path(__file__).resolve().parents[1]
    if args.profile:
        profile = args.profile.expanduser().resolve()
    else:
        profile_root = home / ".config/zen"
        ini = configparser.ConfigParser()
        ini.read(profile_root / "installs.ini")
        profiles = {str((profile_root / ini.get(section, "Default")).resolve()) for section in ini.sections() if ini.has_option(section, "Default")}
        if len(profiles) != 1:
            raise SystemExit("Choose the actual profile using --profile; no settings changed.")
        profile = Path(profiles.pop())
    state = home / ".local/state/zen-rice"
    before = json.loads((state / "managed-preferences.before.json").read_text())
    desired = json.loads((source / "preferences.json").read_text())
    prefs_file = profile / "prefs.js"
    text = prefs_file.read_text()
    current = {}
    for line in text.splitlines():
        match = re.fullmatch(r'user_pref\("([^"\n]+)",\s*(.*)\);', line)
        if match and match[1] in desired:
            current[match[1]] = json.loads(match[2])
    changed = [key for key, value in desired.items() if current.get(key) != value]
    restore_keys = set(desired) - set(changed)
    links = []
    for name in (source / "chrome").glob("*.css"):
        target = profile / "chrome" / name.name
        if target.exists() or target.is_symlink():
            if not target.is_symlink() or target.resolve() != name.resolve():
                raise SystemExit("Custom CSS has changed; review first: " + name.name)
            links.append(target)
    if args.check:
        print(f"Rollback checks passed: {len(restore_keys)} preferences and {len(links)} owned CSS links. No changes.")
        if changed:
            print("Later preference changes will be preserved: " + ", ".join(changed))
        return
    if subprocess.run(["pgrep", "-x", "zen"], capture_output=True).returncode == 0:
        raise SystemExit("Close Zen normally before restoring preferences. Browser data will remain intact.")
    backup = state / "backups" / (datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + f"-rollback-{os.getpid()}")
    backup.mkdir(parents=True, mode=0o700)
    shutil.copy2(prefs_file, backup / "prefs.js")
    kept = []
    for line in text.splitlines(keepends=True):
        match = re.match(r'user_pref\("([^"\n]+)",', line)
        if not match or match[1] not in restore_keys:
            kept.append(line)
    for key in restore_keys:
        old = before[key]
        if old["user"]:
            kept.append(f'user_pref({json.dumps(key)}, {json.dumps(old["value"])});\n')
    temporary = prefs_file.with_name(".prefs-symphony-rollback.tmp")
    with temporary.open("x") as handle:
        handle.write("".join(kept))
    os.chmod(temporary, prefs_file.stat().st_mode & 0o777)
    os.replace(temporary, prefs_file)
    for link in links:
        link.unlink()
    print("Managed CSS and preferences restored. Workspaces, tabs, bookmarks, passwords and sessions preserved.")
    print(f"Backup of pre-rollback preferences: {backup}")


if __name__ == "__main__":
    main()
