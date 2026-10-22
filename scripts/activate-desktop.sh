#!/usr/bin/env bash
set -euo pipefail
if [[ ${1:-} != --apply ]]; then
    printf 'Plan only: reload user units and enable the captured Symphony desktop target, MPD and reader reminders.\n'
    printf 'Run only in your new Arch desktop session: bash scripts/activate-desktop.sh --apply\n'
    exit 0
fi
systemctl --user daemon-reload
# Start the compositor normally through the session manager. The restored unit
# links already describe which services belong to graphical-session.target.
systemctl --user add-wants graphical-session.target symphony-desktop.target
if systemctl --user cat mpd.service >/dev/null 2>&1; then systemctl --user enable mpd.service; fi
if systemctl --user cat mpd-mpris.service >/dev/null 2>&1; then systemctl --user enable mpd-mpris.service; fi
printf 'User units enabled. Log out and enter Hyprland through UWSM; inspect systemctl --user --failed.\n'
