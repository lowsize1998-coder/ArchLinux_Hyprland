#!/usr/bin/env python3
"""Build a static native Telegram Desktop theme from Symphony's GTK palette."""
import argparse
import json
import re
import struct
import zlib
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]


def colors(source):
    entries = dict(re.findall(r"@define-color\s+([\w-]+)\s+([^;]+);", source.read_text()))

    def resolve(key, seen=()):
        if key in seen:
            raise ValueError(f"Color cycle: {key}")
        value = entries[key].strip()
        if value.startswith('@'):
            return resolve(value[1:], (*seen, key))
        if not re.fullmatch(r'#[\da-fA-F]{6}', value):
            raise ValueError(f"Unsupported color {key}: {value}")
        return value.lower()

    return {key: resolve(name) for key, name in {
        'bg': 'background', 'fg': 'foreground', 'panel': 'sidebar_bg_color',
        'muted': 'white', 'border': 'bright_black', 'accent': 'cyan',
    }.items()}


def rgb(value):
    return tuple(int(value[n:n+2], 16) for n in (1, 3, 5))


def mix(a, b, weight):
    return '#' + ''.join(f'{round(x*(1-weight)+y*weight):02x}' for x, y in zip(rgb(a), rgb(b)))


def png(color):
    def chunk(kind, body):
        return struct.pack('!I', len(body)) + kind + body + struct.pack('!I', zlib.crc32(kind + body))
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('!2I5B', 32, 32, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress((b'\0' + bytes(rgb(color))*32)*32)) + chunk(b'IEND', b''))


def build(source):
    c = colors(source)
    c['hover'] = mix(c['panel'], c['fg'], .12)
    c['selected'] = mix(c['panel'], c['fg'], .22)
    c['outgoing'] = mix(c['panel'], c['fg'], .08)
    c['secondary'] = mix(c['panel'], c['fg'], .65)
    definitions = re.findall(r'^([A-Za-z][A-Za-z0-9]*):\s*([^;]+);', (ROOT/'upstream/night.palette').read_text(), re.M)

    # Preserve meaningful safety/status colors and avatar identity colors.
    semantic = re.compile(r'Error|attention|Draft|CallArrow|Peer\d|PeerUserpic|Verified|premium|Premium|reaction|Reaction|Gift|gift|Star|star|stories|Stories|Bot|bot')
    result = {}
    for key, value in definitions:
        value = value.strip()
        if not value.startswith('#') or semantic.search(key):
            result[key] = value
            continue
        original = rgb(value)
        luminance = sum(x*y for x, y in zip(original, (.2126, .7152, .0722)))
        alpha = value[7:] if len(value) == 9 else ''
        if 'Bg' in key or 'Shadow' in key or 'Overlay' in key:
            if 'Selected' in key or 'Active' in key:
                mapped = c['selected']
            elif 'Over' in key or 'Ripple' in key:
                mapped = c['hover']
            elif luminance > 85:
                mapped = c['accent'] if luminance < 215 else c['fg']
            else:
                mapped = c['bg'] if luminance < 23 else c['panel']
        else:
            mapped = c['fg'] if luminance > 185 else c['secondary'] if luminance > 90 else c['border']
        result[key] = mapped + alpha

    # Deliberate roles with sufficient contrast, rather than blind desaturation.
    roles = {
        'windowBg': 'panel', 'windowFg': 'fg', 'windowBgOver': 'hover',
        'windowBgRipple': 'selected', 'windowFgOver': 'fg', 'windowSubTextFg': 'secondary',
        'windowSubTextFgOver': 'muted', 'windowBoldFg': 'fg', 'windowBoldFgOver': 'fg',
        'windowBgActive': 'accent', 'windowFgActive': 'bg', 'windowActiveTextFg': 'muted',
        'windowShadowFgFallback': 'bg', 'activeButtonBg': 'accent', 'activeButtonBgOver': 'muted',
        'activeButtonBgRipple': 'fg', 'activeButtonFg': 'bg', 'activeButtonFgOver': 'bg',
        'activeButtonSecondaryFg': 'panel', 'activeButtonSecondaryFgOver': 'panel',
        'activeLineFg': 'accent', 'lightButtonFg': 'muted', 'lightButtonFgOver': 'fg',
        'outlineButtonOutlineFg': 'accent', 'menuBg': 'panel', 'menuBgOver': 'hover',
        'menuIconFg': 'secondary', 'menuIconFgOver': 'fg', 'menuSeparatorFg': 'border',
        'dialogsBg': 'bg', 'dialogsBgOver': 'panel', 'dialogsBgActive': 'selected',
        'dialogsNameFgActive': 'fg', 'dialogsDateFgActive': 'muted', 'dialogsTextFgActive': 'muted',
        'dialogsTextFgServiceActive': 'fg', 'dialogsUnreadBg': 'accent', 'dialogsUnreadBgOver': 'muted',
        'dialogsUnreadFg': 'bg', 'dialogsUnreadBgMuted': 'border', 'dialogsUnreadFgActive': 'bg',
        'dialogsTextFgService': 'muted', 'dialogsTextFgServiceOver': 'fg',
        'dialogsSentIconFg': 'accent', 'dialogsSentIconFgOver': 'muted',
        'dialogsOnlineBadgeFg': 'accent', 'dialogsOnlineBadgeFgActive': 'fg',
        'historyTextInFg': 'fg', 'historyTextOutFg': 'fg', 'historyTextInFgSelected': 'fg',
        'historyTextOutFgSelected': 'fg', 'historyLinkInFg': 'muted', 'historyLinkOutFg': 'fg',
        'historyLinkInFgSelected': 'fg', 'historyLinkOutFgSelected': 'fg',
        'msgInBg': 'panel', 'msgOutBg': 'outgoing', 'msgInBgSelected': 'selected',
        'msgOutBgSelected': 'selected', 'msgInDateFg': 'secondary', 'msgOutDateFg': 'secondary',
        'msgServiceFg': 'fg', 'msgServiceBg': 'panel', 'msgServiceBgSelected': 'selected',
        'msgInMonoFg': 'muted', 'msgOutMonoFg': 'fg', 'msgInServiceFg': 'muted',
        'msgOutServiceFg': 'fg', 'sideBarBg': 'bg', 'sideBarBgActive': 'selected',
        'sideBarBgRipple': 'hover', 'emojiPanBg': 'panel', 'emojiPanCategories': 'panel',
        'emojiPanHeaderBg': 'panel', 'emojiPanHeaderFg': 'secondary', 'emojiIconFgActive': 'accent',
        'historyUnreadBarBg': 'panel', 'titleBg': 'bg', 'titleBgActive': 'panel',
        'toastFg': 'fg', 'mediaviewMenuFg': 'fg', 'mediaviewControlFg': 'fg',
        'mediaviewFileExtFg': 'fg', 'mainMenuCloudFg': 'fg',
        'dialogsUnreadBgMuted': 'accent', 'dialogsUnreadBgMutedOver': 'muted',
        'sideBarTextFgActive': 'fg', 'sideBarIconFgActive': 'fg',
        'radialFg': 'fg', 'titleButtonCloseFgOver': 'fg', 'stickerPanDeleteFg': 'fg',
        'historyForwardChooseFg': 'fg', 'historyPeerUserpicFg': 'fg', 'youtubePlayIconFg': 'fg',
    }
    unknown = roles.keys() - result.keys()
    if unknown:
        raise ValueError(f'Unsupported Telegram keys: {unknown}')
    result.update({key: c[role] for key, role in roles.items()})
    # Selected chat text must remain light despite dark text on filled action buttons.
    for key in result:
        if key.startswith('dialogs') and key.endswith('FgActive') and key != 'dialogsUnreadFgActive':
            result[key] = c['fg']
        if key.startswith('msg') and (key.endswith('FgSelected') or key.endswith('SelColor')):
            result[key] = c['fg']
    resolved = {}
    for key, value in result.items():
        if value.startswith('#'):
            if not re.fullmatch(r'#[\da-fA-F]{6}([\da-fA-F]{2})?', value):
                raise ValueError(f'Invalid {key}: {value}')
            resolved[key] = value
        else:
            if value not in resolved:
                raise ValueError(f'Invalid or forward reference {key}: {value}')
            resolved[key] = resolved[value]
    output = '// Symphony Zen · generated from shared GTK colors. Telegram Desktop 7.2.9.\n'
    output += '// Base keys: official night theme; see upstream/README.md.\n'
    output += '\n'.join(f'{key}: {value};' for key, value in result.items()) + '\n'
    return output, c, resolved


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path.home()/'.config/symphony/current/.config/gtk-3.0/colors.css')
    args = parser.parse_args()
    content, c, resolved = build(args.source)
    directory = ROOT/'themes'
    directory.mkdir(parents=True, exist_ok=True)
    (directory/'symphony-zen.tdesktop-palette').write_text(content)
    (directory/'background.png').write_bytes(png(c['bg']))
    with ZipFile(directory/'symphony-zen.tdesktop-theme', 'w', ZIP_DEFLATED) as archive:
        archive.writestr('colors.tdesktop-theme', content)
        archive.writestr('background.png', png(c['bg']))
    (directory/'palette.json').write_text(json.dumps(c, indent=2)+'\n')
    print(f'Validated {len(resolved)} colors; theme: {directory}/symphony-zen.tdesktop-theme')


if __name__ == '__main__':
    main()
