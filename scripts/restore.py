#!/usr/bin/env python3
"""Restore the exported home configuration. Default is a read-only plan."""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import os
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
SOURCE_HOME = '/home/rozetta'

def verify():
    manifest = json.loads((ROOT / 'inventory/checksums.json').read_text())
    for relative, entry in manifest.items():
        path = ROOT / relative
        if entry['type'] == 'symlink':
            if not path.is_symlink() or os.readlink(path) != entry['target']:
                raise RuntimeError('Changed link: ' + relative)
        elif not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != entry['sha256']:
            raise RuntimeError('Changed or missing file: ' + relative)
    return len(manifest)

def leaves(path):
    if path.is_symlink() or path.is_file():
        yield path
    elif path.is_dir():
        for child in sorted(path.iterdir()):
            yield from leaves(child)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='Write files, backing up replaced targets')
    parser.add_argument('--home', type=Path, default=Path.home(), help='Destination home (also usable for an isolated restore test)')
    parser.add_argument('--vault', type=Path, help='Existing Obsidian vault; only .obsidian config is restored')
    parser.add_argument('--zen-profile', type=Path, help='Existing, closed Zen profile; restores CSS and selected preferences')
    parser.add_argument('--verify', action='store_true', help='Verify snapshot checksums only')
    args = parser.parse_args()
    checked = verify()
    if args.verify:
        print(f'Checksums verified: {checked} entries');return
    home = args.home.expanduser().absolute()
    if home == Path('/') or home == ROOT or home == ROOT/'home':
        parser.error('Choose a separate destination home')
    if args.apply and os.geteuid() == 0:
        parser.error('Run as the desktop user, without sudo')
    jobs = [(p, home/p.relative_to(ROOT/'home')) for p in leaves(ROOT/'home')]
    if args.vault:
        vault = args.vault.expanduser().resolve()
        if not vault.is_dir():parser.error('--vault must be an existing vault directory')
        jobs += [(p, vault/p.relative_to(ROOT/'profiles/obsidian')) for p in leaves(ROOT/'profiles/obsidian/.obsidian')]
    if args.zen_profile:
        zen = args.zen_profile.expanduser().resolve()
        if not zen.is_dir():parser.error('--zen-profile must already exist; create it by starting Zen first')
        jobs += [(p, zen/p.relative_to(ROOT/'profiles/zen')) for p in leaves(ROOT/'profiles/zen') if p.name != 'user.js']
        jobs.append((ROOT/'profiles/zen/user.js',zen/'user.js'))
    conflicts = sum(target.exists() or target.is_symlink() for _, target in jobs)
    print(f'Validated: {checked}; restore entries: {len(jobs)}; existing targets: {conflicts}')
    print('Destination:', home)
    if not args.apply:
        print('PLAN ONLY. Add --apply to restore; no files were changed.')
        if not args.vault:print('Obsidian payload is saved separately; pass --vault to apply it.')
        if not args.zen_profile:print('Zen payload is saved separately; pass --zen-profile after installing/starting Zen.')
        return
    backup = home/'.local/state/arch-restore/backups'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    backup.mkdir(parents=True,mode=0o700)
    journal=[]
    def preserve(target):
        if not (target.exists() or target.is_symlink()):return
        slot=backup/f'{len(journal):06}'
        shutil.move(str(target),str(slot))
        journal.append({'target':str(target),'backup':str(slot)})
        (backup/'restore-map.json').write_text(json.dumps(journal,ensure_ascii=False,indent=2)+'\n')
    def parents(target):
        if target.parent == target:return
        if target.parent.is_symlink() or (target.parent.exists() and not target.parent.is_dir()):
            preserve(target.parent)
        if not target.parent.exists():
            parents(target.parent);target.parent.mkdir(exist_ok=True)
    for source,target in jobs:
        parents(target)
        data = None
        if not source.is_symlink():
            data = source.read_bytes()
            try:data=data.decode('utf-8').replace(SOURCE_HOME,str(home)).replace('/run/user/1000/',f'/run/user/{os.getuid()}/').encode('utf-8')
            except UnicodeDecodeError:pass
            if args.zen_profile and target == args.zen_profile.expanduser().resolve()/'user.js' and target.is_file():
                # Keep unrelated preferences; replace only keys present in the safe export.
                keys=set(re.findall(rb'user_pref\("([^"]+)"',data))
                original=target.read_bytes().splitlines(keepends=True)
                kept=[]
                for line in original:
                    key=re.match(rb'\s*user_pref\("([^"]+)"',line)
                    if not key or key.group(1) not in keys:kept.append(line)
                data=b''.join(kept)+b'\n'+data
        preserve(target)
        if source.is_symlink():
            # Preserve chains through symphony/current instead of pinning every
            # link to the current theme's ultimate target.
            resolved=Path(os.path.abspath(source.parent / os.readlink(source)))
            if resolved.is_relative_to(ROOT/'home'):
                mapped=home/resolved.relative_to(ROOT/'home')
                target.symlink_to(os.path.relpath(mapped,target.parent))
            elif os.path.isabs(os.readlink(source)):
                target.symlink_to(os.readlink(source))
            else:
                target.symlink_to(os.readlink(source))
        else:
            target.write_bytes(data)
            target.chmod(source.stat().st_mode & 0o777)
    print('Restored entries:',len(jobs))
    print('Replaced-file backup:',backup)
    print('Services and system files were not changed. Continue with docs/RESTORE.md.')

if __name__ == '__main__':
    main()
