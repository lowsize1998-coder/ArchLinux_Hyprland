#!/usr/bin/env bash
set -euo pipefail
source_dir="$(cd -- "$(dirname -- "$0")" && pwd)"
target_dir="$HOME/.local/lib/spotify-dreamcore"
mkdir -p "$target_dir"
/usr/lib/qt6/moc "$source_dir/spotify-mini.cpp" -o "$target_dir/spotify-mini.moc"
g++ -O2 -fPIC -std=c++17 "$source_dir/spotify-mini.cpp" -I"$target_dir" \
    $(pkg-config --cflags --libs Qt6Widgets Qt6DBus Qt6Network) -o "$target_dir/spotify-mini"
