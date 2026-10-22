#!/usr/bin/env bash
set -euo pipefail
repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
if [[ ${1:-} != --apply ]]; then
    printf 'Plan only: unpack Waybar 0.15.0, apply the two saved native patches, build and install into ~/.local/lib.\n'
    printf 'Requires Meson, Ninja, patch, unzip and Waybar development dependencies.\n'
    exit 0
fi
for tool in meson ninja patch unzip; do command -v "$tool" >/dev/null || { printf 'Missing tool: %s\n' "$tool" >&2; exit 1; }; done
cache_dir="${XDG_CACHE_HOME:-$HOME/.cache}/arch-restore"
mkdir -p "$cache_dir"
task_build_dir=$(mktemp -d "$cache_dir/waybar-XXXXXXXX")
unzip -q "$repo_dir/build/waybar/waybar-0.15.0.zip" -d "$task_build_dir"
source_dir="$task_build_dir/Waybar-0.15.0"
patch -d "$source_dir" -p1 < "$repo_dir/build/waybar/5013-native.patch"
patch -d "$source_dir" -p1 < "$repo_dir/build/waybar/5043-native.patch"
meson setup "$task_build_dir/build" "$source_dir" --buildtype=release \
    -Dtests=disabled -Dman-pages=disabled -Dsystemd=disabled -Dcava=disabled \
    -Dpulseaudio=enabled -Dmpris=enabled -Ddbusmenu-gtk=enabled
ninja -C "$task_build_dir/build"
install -Dm755 "$task_build_dir/build/waybar" "$HOME/.local/lib/waybar-lua-0.15.0/waybar"
printf 'Built and installed user-local Waybar. Restart the user service in your desktop session.\n'
