# Dolphin · Dreamcore Charcoal

Native KDE color scheme matching the dark Zen browser chrome:
background `#131313`, cream text `#FAEEBA`, controls `#191919`,
selection `#2F2D27`, muted text `#A9A180`.

`DreamcoreCharcoal.colors` is linked from
`~/.local/share/color-schemes/DreamcoreCharcoal.colors`.
Only Dolphin selects it, through `~/.config/dolphinrc`:

```ini
[UiSettings]
ColorScheme=DreamcoreCharcoal
```

Shared Qt6ct settings, other apps, and the Symphony Zen theme are unchanged.
A native Dolphin restart applies color-file edits. No custom launch wrapper,
stylesheet, background service, or extra package is required.

The previous Dolphin configuration is backed up under
`~/.local/state/dolphin-dark/backups/`.
