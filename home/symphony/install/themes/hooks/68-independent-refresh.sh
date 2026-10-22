#!/bin/bash
set -euo pipefail
# Reload styles without restarting foreground apps or browser sessions.
command -v swaync-client >/dev/null && swaync-client -rs >/dev/null 2>&1 || true
# SwayOSD has no CSS reload API. Replace only its existing OSD daemon.
if pgrep -x swayosd-server >/dev/null; then
    pkill -TERM -x swayosd-server
    for _ in {1..10}; do
        pgrep -x swayosd-server >/dev/null || break
        sleep 0.05
    done
    hyprctl dispatch 'hl.dsp.exec_cmd("swayosd-server")' >/dev/null
fi
if [[ -f "$CURRENT_LINK/.config/zathura/appearance" && -f "$HOME/.config/zathura/rice.py" ]]; then
    python3 - <<'PY'
import importlib.util
from pathlib import Path
p=Path.home()/'.config/zathura/rice.py'
spec=importlib.util.spec_from_file_location('rice',p)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.refresh()
PY
fi
exit 0
