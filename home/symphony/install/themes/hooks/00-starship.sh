#!/bin/bash
# starship - symlink config
src="$CURRENT_LINK/.config/starship.toml"
[[ -f "$src" ]] || exit 0
ln -sf "$src" "$HOME/.config/starship.toml"
