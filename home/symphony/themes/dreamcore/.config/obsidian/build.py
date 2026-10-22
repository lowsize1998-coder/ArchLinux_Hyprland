#!/usr/bin/env python3
"""Build a standalone Obsidian theme from the existing Dreamcore palette."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
THEME = HERE.parents[1]
palette = json.loads((THEME / "palette.json").read_text())
derived = json.loads((THEME / "derived.json").read_text())
colors = {
    "bg": palette["background"],
    "text": palette["text"],
    "secondary": palette["secondary_text"],
    "pink": palette["panel"],
    "selection": palette["selection"],
    "teal": palette["secondary_accent"],
    "info": palette["info"],
    "success": palette["success"],
    "warning": palette["warning"],
    "ink": derived["ink"],
    "muted": derived["dim_text_on_blue"],
    "accent": derived["accent_on_blue"],
    "error": derived["error_on_blue"],
}
# Derive quiet surfaces without introducing a second palette.
def mix(a, b, fraction):
    return "#" + "".join(f"{round(int(a[i:i+2], 16) * (1-fraction) + int(b[i:i+2], 16) * fraction):02X}" for i in (1, 3, 5))

colors["surface"] = mix(colors["bg"], "#000000", 0.24)
colors["hover"] = mix(colors["bg"], colors["text"], 0.09)
colors["border"] = mix(colors["bg"], colors["secondary"], 0.18)
css = "/* Generated from Dreamcore palette.json by .config/obsidian/build.py. */\nbody {\n"
css += "".join(f"  --dream-{key}: {value};\n" for key, value in colors.items())
css += "}\n\n"
for name in ("chrome.css", "editor.css", "focus.css"):
    css += (HERE / name).read_text() + "\n"
(HERE / "theme.css").write_text(css)
(HERE / "manifest.json").write_text(json.dumps({
    "name": "Dreamcore", "version": "1.0.0", "minAppVersion": "1.9.0", "author": "Rozetta"
}, indent=2) + "\n")
print(HERE / "theme.css")
