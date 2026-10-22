#!/usr/bin/env bash
set -euo pipefail
repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
if [[ ${1:-} != --apply ]]; then
    printf 'Plan only. This installs the explicit official Arch packages and performs a full upgrade.\n'
    printf 'Review inventory/packages-native-explicit.txt, then run: bash scripts/install-packages.sh --apply\n'
    exit 0
fi
mapfile -t packages < "$repo_dir/inventory/packages-native-explicit.txt"
sudo pacman -Syu --needed -- "${packages[@]}"
printf '\nForeign/AUR packages are listed in inventory/packages-foreign-explicit.txt.\n'
printf 'Review their PKGBUILDs before installing them with your AUR helper.\n'
