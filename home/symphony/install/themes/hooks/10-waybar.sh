#!/bin/bash
set -e
src="$CURRENT_LINK/.config/waybar/colors.css"
[[ -f "$src" ]] || exit 0
ln -sf "$src" "$HOME/.config/waybar/colors.css"
systemctl --user try-restart symphony-waybar.service
