#!/usr/bin/env python3
"""Build an app-only Qt resource palette from the shared Dreamcore colors."""
import json
from pathlib import Path
import subprocess
import sys
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parent
THEME = ROOT.parent.parent


def mix(first, second, weight):
    return '#' + ''.join(f'{round(int(first[i:i+2], 16) * (1-weight) + int(second[i:i+2], 16) * weight):02X}' for i in (1, 3, 5))


def main():
    output = Path(sys.argv[1])
    output.mkdir(parents=True, exist_ok=True)
    palette = json.loads((THEME / 'palette.json').read_text())
    derived = json.loads((THEME / 'derived.json').read_text())
    roles = {**palette, 'background': palette['background'],
             'hover': mix(palette['background'], palette['secondary_accent'], .12),
             'selected': mix(palette['background'], palette['accent'], .18),
             'border': mix(palette['background'], palette['border'], .35),
             'muted': derived['dim_text_on_blue'], 'ink': derived['ink'],
             'accent_pressed': mix(palette['accent'], palette['secondary_accent'], .25),
             'popup': palette['background'], 'error': derived['error_on_blue']}
    mapping = json.loads((ROOT / 'color-roles.json').read_text())
    properties = {}
    for role, names in mapping.items():
        for name in names.split():
            if name in properties:
                raise ValueError('Duplicate color role: ' + name)
            properties[name] = roles[role]
    resource = ET.Element('RCC')
    group = ET.SubElement(resource, 'qresource', prefix='/imports/Theme')
    for name in ('DarkTheme', 'LightTheme'):
        lines = ['pragma Singleton', 'import QtQuick 2.15', 'Item {',
                 '  readonly property string prefix: "dark"']
        lines += [f'  readonly property color {key}: "{color}"' for key, color in properties.items()]
        lines += ['}', '']
        (output / (name + '.qml')).write_text('\n'.join(lines))
        ET.SubElement(group, 'file', alias=name + '.qml').text = name + '.qml'
    ET.ElementTree(resource).write(output / 'theme.qrc', encoding='utf-8')
    subprocess.run(['/usr/lib/qt6/rcc', '--binary', '--no-compress', '-o', str(output / 'theme.rcc'), str(output / 'theme.qrc')], check=True)
    (output / 'colors.json').write_text(json.dumps(properties, indent=2) + '\n')
    print(f'Built Happ palette: {len(properties)} color properties')


if __name__ == '__main__':
    main()
