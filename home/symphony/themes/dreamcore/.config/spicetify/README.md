# Dreamcore Spotify

The official Spotify client is customized by Spicetify 2.45.3.
Colors come from the theme's palette.json and derived.json. After palette edits,
the theme's build.py regenerates Themes/symphony/user.css from user.css.in.

## Selected behavior

- 16 px body text, roomier lists, 140 ms hover color transitions.
- All Spotify UI surfaces use the central blue #194B66, with cream text and outline selection.
- Homepage promotional banners are hidden; their embedded videos are paused.
- Music-only homepage; podcast/audiobook filters and social/update buttons hidden.
- Smooth progress and volume indicators, immediate response while dragging.
- Volume wheel: 2%; Ctrl: 1%; Shift: 5%. No numeric display or entry.
- Standard Spotify keyboard shortcuts; no seek-on-wheel or extra hotkeys.
- Crossfade 3 seconds; Automix on; normalization off; Very High streaming quality;
  automatic quality reduction off. These are saved in native Spotify settings.
- Native Spotify lyrics. No statistics, library exports, sleep timer or auto-skip.

## Extensions

dreamcore-shuffle.js is a local adaptation of Spicetify's bundled Shuffle+.
Use "Play with Shuffle+" in a playlist's context menu. It starts the shuffled
first track directly, waits for playback/queue commands, and disables native
shuffle so Spotify preserves the supplied order. The ordinary Play button
retains Spotify's native behavior. The upstream shuffle+.js stays unchanged.
dreamcore-controls.js contains local wheel handling and the music-only home filter.
dreamcore-display.js is a local adaptation of Spicetify's MIT Full App Display:
static background, no blurred canvas rendering, progress/controls and next
track information. The cover grows up to 560 px and adapts to the window size.
The large player's volume row is removed; normal Spotify volume controls remain.
The activator is the Full App Display button in Spotify's
bottom playback bar (projector icon). Double-click the view, or press Escape, to exit. It fills the Spotify
window; Hyprland's existing Super+F can make that window fullscreen.
There are no remote script loaders or new always-on extension animation loops.

## Headphone equalizer

The native Spotify six-band EQ is enabled only inside Spotify:

| Frequency | Gain |
| --- | --- |
| 60 Hz | 0 dB |
| 150 Hz | -4 dB |
| 400 Hz | -2 dB |
| 1 kHz | -2 dB |
| 2.4 kHz | -3 dB |
| 15 kHz | -8 dB |

This is a conservative starting point for the user's DT 990 Pro 80-ohm headphones:
more low bass relative to the mids, less upper-frequency emphasis. The broad
shape was informed by AutoEq/oratory1990's DT 990 Pro family result, not by a
dedicated measurement of this 80-ohm unit. The six broad native bands cannot
reproduce the original ten parametric filters. Gains use cuts rather than boosts.
Refine by listening; the native settings remain editable.

Reference: https://github.com/jaakkopasanen/AutoEq/tree/master/results/oratory1990/over-ear/Beyerdynamic%20DT%20990%20Pro
The actual connected DAC identifies itself as FiiO KA13.

## Mini-player

Launch **Spotify Mini** from Rofi or run ~/.local/bin/spotify-mini.
It is a small native Qt/Wayland MPRIS controller of the official Spotify process;
it does not implement another Spotify client, log in, or read account files.
It loads current metadata/artwork and updates on D-Bus property changes.
Only Spotify CDN cover artwork is downloaded. It has no polling timer.
The window opens/moves to the monitor of invocation; it floats without pinning
or an always-on-top flag. It closes independently of Spotify.

Rebuild after a Qt upgrade if needed: ./build-mini.sh
Source: spotify-mini.cpp. Binary: ~/.local/lib/spotify-dreamcore/spotify-mini.
Launcher: ~/.local/bin/spotify-mini. Desktop file: ~/.local/share/applications/dreamcore-spotify-mini.desktop.
Hyprland window rule: the spotify-mini block in ~/.config/hypr/local.lua.

## Recovery and private data

Backup manifest: the directory named in ~/.local/state/spotify-dreamcore/agreed-backup-path.
Native Spotify settings are backed up privately and must not enter dotfiles.
No passwords, cookies, sessions or tokens belong in this theme directory.
Spicetify can require reapplication after Spotify updates (`spicetify backup apply`).
The initial backup and generated verification files live in ~/.local/state/spotify-dreamcore.
