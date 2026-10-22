#!/bin/sh
set -eu
source_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
output_dir="$HOME/.local/lib/happ-dreamcore"
mkdir -p "$output_dir"
# Use Happ's bundled Qt at runtime, not a different system Qt version.
g++ -O2 -shared -fPIC -DQT_NO_VERSION_TAGGING "$source_dir/resource-loader.cpp" -o "$output_dir/resource-loader.so" \
    $(pkg-config --cflags --libs Qt6Core) -Wl,-rpath,/opt/happ/lib
