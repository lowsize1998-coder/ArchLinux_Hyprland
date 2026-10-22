#!/bin/bash
set -euo pipefail
config_dir="$HOME/.config/zen-rice"
[[ -f "${CURRENT_LINK:-$HOME/.config/symphony/current}/.config/zen-browser/chrome/userChrome.css" ]] && exit 0
source_palette="${CURRENT_LINK:-$HOME/.config/symphony/current}/.config/gtk-3.0/colors.css"
[[ -f "$config_dir/scripts/build-colors.py" && -f "$source_palette" ]] || exit 0
python3 "$config_dir/scripts/build-colors.py" --source "$source_palette"
# Generated CSS is picked up on the next browser restart; never restart user sessions here.
