#!/usr/bin/env python3
"""Translate the active Symphony GTK palette into browser CSS variables."""
import argparse
import json
import os
import re
import tempfile
from pathlib import Path

TOKENS = {
    "bg": "background", "fg": "foreground", "panel": "sidebar_bg_color",
    "raised": "card_bg_color", "muted": "white", "border": "bright_black",
    "accent": "cyan", "accent-ink": "background",
}


def read_palette(source):
    definitions = dict(re.findall(r"@define-color\s+([\w-]+)\s+([^;]+);", source.read_text()))

    def resolve(name, seen=()):
        if name in seen:
            raise ValueError(f"Cyclic color definition: {name}")
        value = definitions.get(name, "").strip()
        if re.fullmatch(r"#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3}(?:[0-9a-fA-F]{2})?)?", value):
            return value.lower()
        if re.fullmatch(r"@[\w-]+", value):
            return resolve(value[1:], (*seen, name))
        raise ValueError(f"Unsupported or missing Symphony color: {name}")

    return {token: resolve(name) for token, name in TOKENS.items()}


def build(source):
    palette = read_palette(source)
    def rgb(value):
        value = value.lstrip("#")
        if len(value) == 3:
            value = "".join(x * 2 for x in value)
        return tuple(int(value[i:i+2], 16) for i in (0, 2, 4))

    def mix(background, foreground, foreground_weight):
        a, b = rgb(background), rgb(foreground)
        return "#" + "".join(f"{round(x * (1-foreground_weight) + y * foreground_weight):02x}" for x, y in zip(a, b))

    # Resolve hover colors once on theme changes, rather than in browser styles.
    palette["hover"] = mix(palette["panel"], palette["fg"], 0.12)
    palette["selected"] = mix(palette["panel"], palette["fg"], 0.22)
    scheme = "dark" if sum(rgb(palette["bg"])) < 384 else "light"
    lines = [
        "/* Generated from the active Symphony GTK palette; run build-colors.py. */",
        '@-moz-document url("chrome://browser/content/browser.xhtml"),',
        '  url("about:newtab"), url("about:home"), url("about:preferences"), url("about:downloads") {',
        "  :root {",
    ]
    lines += [f"    --symphony-{key}: {value};" for key, value in palette.items()]
    lines += [
        f"    --symphony-color-scheme: {scheme};",
        f"    --symphony-theme-name: {json.dumps(source.resolve().parents[2].name)};",
        "  }", "}", "",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path.home()/".config/symphony/current/.config/gtk-3.0/colors.css")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1]/"chrome/colors.css")
    args = parser.parse_args()
    content = build(args.source)
    if args.output.exists() and args.output.read_text() == content:
        print("Zen palette is already current.")
        return
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".colors-", suffix=".css", dir=args.output.parent)
    try:
        with os.fdopen(fd, "w") as handle:
            handle.write(content)
        os.chmod(temporary, 0o644)
        os.replace(temporary, args.output)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    print(f"Updated Zen palette: {args.output}")


if __name__ == "__main__":
    main()
