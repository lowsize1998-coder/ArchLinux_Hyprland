#!/bin/bash
set -euo pipefail
src="$CURRENT_LINK/.config/discord/dreamcore.theme.css"
if [[ ! -f "$src" ]]; then
    src="$HOME/symphony/themes/dreamcore/.config/discord/inactive.css"
fi
mkdir -p "$HOME/.config/Vencord/themes"
ln -sfn "$src" "$HOME/.config/Vencord/themes/dreamcore.theme.css"
