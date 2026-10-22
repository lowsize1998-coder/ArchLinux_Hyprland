#!/usr/bin/env python3
"""Build Koodo colors from the active Symphony palette."""
import argparse
import json
import os
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent


def build(source):
    definitions = dict(re.findall(r"@define-color\s+([\w-]+)\s+([^;]+);", source.read_text()))

    def color(key, seen=()):
        value = definitions.get(key, "").strip()
        if key in seen:
            raise ValueError(f"Cyclic palette color: {key}")
        if re.fullmatch(r"#[\da-fA-F]{6}", value):
            return value.lower()
        if value.startswith("@"):
            return color(value[1:], (*seen, key))
        raise ValueError(f"Unsupported palette color: {key} = {value}")

    palette = {key: color(value) for key, value in {
        "background": "background", "foreground": "foreground",
        "panel": "sidebar_bg_color", "accent": "cyan", "border": "bright_black",
    }.items()}
    palette["theme"] = source.resolve().parents[2].name
    return palette


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path.home()/".config/symphony/current/.config/gtk-3.0/colors.css")
    args = parser.parse_args()
    content = json.dumps(build(args.source), ensure_ascii=False, indent=2) + "\n"
    output = ROOT / "palette.json"
    if not output.exists() or output.read_text() != content:
        temporary = output.with_suffix(".tmp")
        temporary.write_text(content)
        os.replace(temporary, output)


if __name__ == "__main__":
    main()
