#!/usr/bin/env python3
"""Install upstream Koodo locally, then attach the Symphony appearance hook."""
import argparse
from datetime import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request

CONFIG = Path(__file__).resolve().parent
BASE = Path.home()/".local/share/koodo-rice"
API = "https://api.github.com/repos/koodo-reader/koodo-reader/releases/latest"


def configure_hyprland():
    local = Path.home()/".config/hypr/local.lua"
    main = local.with_name("hyprland.lua")
    if not main.exists() or not local.exists():
        return
    marker = "-- BEGIN koodo-rice\n"
    content = local.read_text()
    if marker not in content:
        backup = local.with_name("local.lua.before-koodo-rice-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
        shutil.copy2(local, backup)
        content += '\n' + marker + (
            'hl.window_rule({name = "koodo-rice-readable", '
            'match = {class = "^(koodo-reader|Koodo Reader|xyz[.]960960[.]koodo)$"}, '
            'opacity = "1 1"})\n-- END koodo-rice\n'
        )
        local.write_text(content)
    if shutil.which("hyprctl"):
        subprocess.run(["hyprctl", "reload"], check=False, stdout=subprocess.DEVNULL)


def download(url, destination):
    request = urllib.request.Request(url, headers={"User-Agent":"Koodo-Symphony-local-installer", "Accept":"application/vnd.github+json"})
    with urllib.request.urlopen(request, timeout=60) as response, destination.open("wb") as output:
        shutil.copyfileobj(response, output, 1024 * 1024)


def obtain(directory):
    manifest = directory/"release.json"
    download(API, manifest)
    release = json.loads(manifest.read_text())
    if release.get("prerelease") or release.get("draft"):
        raise ValueError("Expected a stable public release")
    architecture = platform.machine()
    candidates = []
    for asset in release.get("assets", []):
        name = asset["name"].lower()
        if not name.endswith(".appimage"):
            continue
        arm = any(token in name for token in ("arm", "aarch"))
        x86_32 = bool(re.search(r"i[3-6]86|ia32|x86(?![_-]?64)", name))
        if architecture == "x86_64" and not arm and not x86_32:
            candidates.append(asset)
        elif architecture == "aarch64" and any(token in name for token in ("arm64", "aarch64")):
            candidates.append(asset)
    if len(candidates) != 1:
        raise ValueError(f"Could not select one AppImage for {architecture}: {[a['name'] for a in candidates]}")
    asset = candidates[0]
    url = asset["browser_download_url"]
    if not url.startswith("https://github.com/koodo-reader/koodo-reader/releases/download/"):
        raise ValueError("Unexpected release download URL")
    image = directory/"Koodo.AppImage"
    print(f"Скачивание {release['tag_name']}: {asset['name']}", flush=True)
    download(url, image)
    if image.stat().st_size != asset["size"]:
        raise ValueError("Downloaded AppImage size does not match the release")
    digest = asset.get("digest")
    if digest:
        if not digest.startswith("sha256:"):
            raise ValueError("Unsupported release digest")
        with image.open("rb") as handle:
            actual = hashlib.file_digest(handle, "sha256").hexdigest()
        if actual != digest.removeprefix("sha256:"):
            raise ValueError("AppImage SHA256 mismatch")
        print("SHA256 совпадает с данными GitHub.", flush=True)
    return image, release["tag_name"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("appimage", nargs="?", type=Path, help="Already downloaded official Koodo AppImage")
    args = parser.parse_args()
    BASE.mkdir(parents=True, exist_ok=True)
    with (BASE/"install.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with tempfile.TemporaryDirectory(prefix=".install-", dir=BASE) as temporary:
            stage = Path(temporary)
            if args.appimage:
                image = stage/"Koodo.AppImage"
                shutil.copyfile(args.appimage.expanduser().resolve(), image)
                version = "local"
            else:
                image, version = obtain(stage)
            image.chmod(0o755)
            print("Распаковка в пользовательский каталог…", flush=True)
            subprocess.run([str(image),"--appimage-extract"], cwd=stage, check=True, stdout=subprocess.DEVNULL)
            appdir = stage/"squashfs-root"
            archives = list(appdir.rglob("resources/app.asar"))
            if len(archives) != 1:
                raise ValueError("Expected one Electron app.asar in the official AppImage")
            archive = archives[0]
            executable = archive.parent.parent/"koodo-reader"
            if not executable.is_file():
                raise ValueError("Cannot locate the upstream koodo-reader executable")
            subprocess.run([sys.executable, str(CONFIG/"patch-asar.py"), str(archive)], check=True)
            subprocess.run([sys.executable, str(CONFIG/"theme.py")], check=True)
            installation = BASE/("release-" + re.sub(r"[^\w.-]", "_", version) + "-" + stage.name.removeprefix(".install-"))
            shutil.move(str(appdir), installation)
            (installation/"rice-executable.txt").write_text(str(executable.relative_to(appdir)))
            (installation/"rice-release.txt").write_text(version + "\n")
            candidate = BASE/".current-new"
            candidate.unlink(missing_ok=True)
            candidate.symlink_to(installation.name)
            os.replace(candidate, BASE/"current")
        configure_hyprland()
        for command in [
            ["update-desktop-database",str(Path.home()/".local/share/applications")],
            ["xdg-mime","default","koodo-rice.desktop","application/pdf"],
            ["xdg-mime","default","koodo-rice.desktop","application/epub+zip"],
            ["xdg-mime","default","koodo-rice.desktop","application/x-fictionbook+xml"],
            ["xdg-mime","default","koodo-rice.desktop","application/x-mobipocket-ebook"],
            ["xdg-mime","default","koodo-rice.desktop","application/vnd.amazon.ebook"],
            ["xdg-mime","default","koodo-rice.desktop","application/vnd.comicbook+zip"],
            ["xdg-mime","default","koodo-rice.desktop","application/vnd.comicbook-rar"],
        ]:
            if shutil.which(command[0]):
                result = subprocess.run(command, check=False)
                if result.returncode:
                    print(f"Не удалось выполнить: {' '.join(command)}",file=sys.stderr)
        print("Установлено. Запуск: koodo-rice. Настройка: ~/.config/koodo-rice/settings.json")
        print("Режимы чтения: Ctrl+Alt+1 — rice, Ctrl+Alt+2 — бумага, Ctrl+Alt+3 — тёплый.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        print(f"Установка не завершена: {error}", file=sys.stderr)
        sys.exit(1)
