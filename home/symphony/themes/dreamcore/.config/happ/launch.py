#!/usr/bin/env python3
"""Launch the official Happ with a GUI-only palette when Dreamcore is active."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
THEME = ROOT.parent.parent
BINARY = Path('/opt/happ/bin/Happ')
OUTPUT = Path.home() / '.local/share/happ-dreamcore'
LOADER = Path.home() / '.local/lib/happ-dreamcore/resource-loader.so'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    environment = os.environ.copy()
    current = Path.home() / '.config/symphony/current'
    if current.resolve() == THEME:
        try:
            manifest = json.loads((OUTPUT / 'compatibility.json').read_text())
            if digest(BINARY) != manifest['binarySha256']:
                print('Happ Dreamcore: app updated; using native colors until the theme is checked.', file=sys.stderr)
            else:
                inputs = [THEME / 'palette.json', THEME / 'derived.json', ROOT / 'color-roles.json', ROOT / 'build-theme.py']
                fingerprint = hashlib.sha256(''.join(digest(path) for path in inputs).encode()).hexdigest()
                marker = OUTPUT / 'palette-fingerprint'
                if not (OUTPUT / 'theme.rcc').exists() or not marker.exists() or marker.read_text().strip() != fingerprint:
                    subprocess.run([sys.executable, str(ROOT / 'build-theme.py'), str(OUTPUT)], check=True)
                    marker.write_text(fingerprint + '\n')
                if LOADER.exists():
                    previous = environment.get('LD_PRELOAD', '')
                    environment['HAPP_DREAMCORE_PREVIOUS_PRELOAD'] = previous
                    environment['LD_PRELOAD'] = str(LOADER) + (':' + previous if previous else '')
                    environment['HAPP_DREAMCORE_RESOURCE'] = str(OUTPUT / 'theme.rcc')
        except (OSError, ValueError, subprocess.CalledProcessError) as error:
            print('Happ Dreamcore: using native colors (' + type(error).__name__ + ').', file=sys.stderr)
    os.execve(BINARY, [str(BINARY), *sys.argv[1:]], environment)


if __name__ == '__main__':
    main()
