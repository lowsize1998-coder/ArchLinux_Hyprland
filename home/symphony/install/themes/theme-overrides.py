#!/usr/bin/env python3
"""Select independent per-theme configs, restoring the originals when absent.

Backups live in private local state, never in a theme or browser data directory.
Destinations are explicit; no recursive profile reads or copies.
"""
import configparser
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

HOME = Path.home()
THEME = Path(os.environ.get('CURRENT_LINK', HOME/'.config/symphony/current'))
STATE = HOME/'.local/state/symphony-theme-overrides'
STATE.mkdir(parents=True, exist_ok=True, mode=0o700)
os.chmod(STATE, 0o700)
DB = STATE/'state.json'
data = json.loads(DB.read_text()) if DB.exists() else {}


def record(path):
    if path.is_symlink(): return {'kind':'link','target':os.readlink(path)}
    if path.exists():
        if not path.is_file(): raise RuntimeError(f'Not a regular config: {path}')
        payload=path.read_bytes()
        key=hashlib.sha256(payload).hexdigest()
        backup=STATE/key
        if not backup.exists():
            backup.write_bytes(payload)
            backup.chmod(0o600)
        return {'kind':'file','backup':key,'mode':path.stat().st_mode&0o777}
    return {'kind':'absent'}


def replace(path, item):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp=path.with_name('.'+path.name+f'.theme-{os.getpid()}')
    if temp.exists() or temp.is_symlink(): raise RuntimeError(f'Temporary path exists: {temp}')
    try:
        if item['kind']=='link': temp.symlink_to(item['target'])
        elif item['kind']=='file':
            shutil.copyfile(STATE/item['backup'],temp)
            temp.chmod(item['mode'])
        else:
            path.unlink(missing_ok=True)
            return
        os.replace(temp,path)
    finally:
        if temp.exists() or temp.is_symlink(): temp.unlink()


paths = {HOME/'.config'/p:THEME/'.config'/p for p in (
    'waybar/style.css','waybar/config.jsonc','waybar/scripts/keyboard-layout',
    'rofi/config.rasi','swaync/style.css',
    'swayosd/style.css','hypr/hyprlock.conf','qt6ct/qt6ct.conf',
    'zathura/appearance','zathura/profiles/default','zathura/profiles/rice')}
for kind in ('search','clipboard','emoji','keybinds','powermenu','power-profiles','rofi-Beats','rofi-Beats-menu','theme-picker','wallpaper'):
    rel=f'rofi/custom-rofi/config-{kind}.rasi'
    paths[HOME/'.config'/rel]=THEME/'.config'/rel
profiles = HOME/'.config/zen/profiles.ini'
if profiles.exists():
    ini=configparser.ConfigParser()
    ini.read(profiles)
    # Installation-selected profile takes precedence over legacy Default flags.
    profile=next((ini[s]['Default'] for s in ini.sections() if s.startswith('Install') and ini.has_option(s,'Default')),None)
    if profile:
        root=Path(profile) if Path(profile).is_absolute() else profiles.parent/profile
        if root.exists():
            for file in ('userChrome.css','userContent.css'):
                paths[root/'chrome'/file]=THEME/'.config/zen-browser/chrome'/file

# Validate every owned destination before touching any of them.
for key, item in data.items():
    dest=Path(key)
    if not dest.is_symlink() or os.readlink(dest)!=item['active']:
        raise RuntimeError(f'Config changed outside theme switching; preserved: {dest}')

planned=[]
updated=dict(data)
for dest, src in paths.items():
    key=str(dest)
    item=data.get(key)
    if src.is_file():
        target=str(src.resolve())
        if item and item['active']==target: continue
        original=item['original'] if item else record(dest)
        updated[key]={'original':original,'active':target}
        planned.append((dest,{'kind':'link','target':target}))
    elif item:
        planned.append((dest,item['original']))
        del updated[key]
if '--check' in sys.argv:
    print(f'Theme overrides: preflight OK ({len(planned)} selections)')
    sys.exit(0)
previous=[(dest,record(dest)) for dest,_ in planned]
try:
    for dest, selection in planned: replace(dest,selection)
    temp=DB.with_suffix('.tmp')
    temp.write_text(json.dumps(updated,indent=2)+'\n')
    temp.chmod(0o600)
    os.replace(temp,DB)
except Exception:
    for dest, item in reversed(previous): replace(dest,item)
    raise
print(f'Theme overrides: {len(planned)} configs selected/restored')
