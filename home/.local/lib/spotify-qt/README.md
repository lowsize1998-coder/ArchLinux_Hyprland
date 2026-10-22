# Spotify Qt on this desktop

Installed portable official release v4.0.4 with its bundled Qt and native Wayland.
The AppImage SHA-256 matches the digest published in the GitHub release metadata.
Librespot 0.8.0-5 is extracted from the official Arch package; its pacman signature
was verified. These are local installations, not pacman-managed packages.

Launch: Spotify Qt in Rofi, or ~/.local/bin/spotify-qt.
Super+M was returned to official Spotify when that client was selected instead.
The existing Spotify installation remains available.

Theme source: ~/symphony/themes/dreamcore/palette.json and derived.json.
QSS template: .config/spotify-qt/dreamcore.qss.in inside that theme.
Generate QSS: python3 ~/symphony/themes/dreamcore/.config/spotify-qt/build-style.py
The normal Dreamcore build.py also regenerates it.
Restart the app after switching themes. If the selected theme has no Spotify Qt
stylesheet, the launcher uses the app's normal Fusion appearance.

## First login

Create your own application at https://developer.spotify.com/dashboard.
Select Web API and register the Redirect URI exactly as http://127.0.0.1:8888.
Enter Client ID and Client secret directly into Spotify Qt, then Authenticate.
Never put these keys in chat, screenshots, or a dotfiles repository.
If librespot opens a second Spotify authorization page, complete that login too.
The audio device will appear as spotify-qt@<hostname> in Spotify Connect.

## Prepared playback settings

Backend: pulseaudio through the installed PipeWire PulseAudio compatibility server.
Quality: 320 kbit/s. Initial client volume: 50%. Audio cache limit: 512 MiB.
Librespot starts with the app and stops with it; no always-on service was added.
MPRIS is enabled for the existing Waybar music module and playerctl.
Actual playback and MPRIS need checking after user authentication.

LAN discovery is disabled: librespot's libmdns backend failed to bind UDP 5353,
which is used by kdeconnectd on this desktop. Spotify account-based Connect and
the backend's browser OAuth login remain available. KDE Connect was not changed.

## Private data and recovery

Private account configuration: ~/.config/kraxarn/spotify-qt.json (mode 600).
Private runtime cache: ~/.cache/kraxarn/spotify-qt, including librespot credentials.
Neither belongs in dotfiles. The launcher uses umask 077 for new private files.
Configuration backup manifest and verification: ~/.local/state/spotify-qt-setup.
The previous Hyprland local.lua and Dreamcore build.py/README.md are backed up
under the path recorded in ~/.local/state/spotify-qt-setup/backup-path.
Zen theme files were checked unchanged.

Updates are manual: download and verify a new official release, then replace the
portable app after closing it. Librespot's local copy also needs manual updates.
