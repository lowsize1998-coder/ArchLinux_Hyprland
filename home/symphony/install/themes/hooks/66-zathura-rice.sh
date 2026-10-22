#!/bin/bash
set -euo pipefail
config="$HOME/.config/zathura"
[[ -f "${CURRENT_LINK:-$HOME/.config/symphony/current}/.config/zathura/appearance" ]] && exit 0
[[ -f "$config/rice.py" ]] || exit 0
python3 "$config/rice.py" build --live --source "${CURRENT_LINK:-$HOME/.config/symphony/current}/.config/gtk-3.0/colors.css"
