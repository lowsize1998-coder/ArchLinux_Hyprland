#!/usr/bin/env python3
"""Generate spotify-qt's app-only QSS from Dreamcore's shared palette."""
import json
from pathlib import Path
from string import Template

HERE = Path(__file__).resolve().parent
THEME = HERE.parent.parent
colors = json.loads((THEME / 'palette.json').read_text())
colors.update(json.loads((THEME / 'derived.json').read_text()))
stylesheet = Template((HERE / 'dreamcore.qss.in').read_text()).substitute(colors)
(HERE / 'dreamcore.qss').write_text(stylesheet)
