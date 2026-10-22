# Dreamcore

Independent theme built from fourteen user-selected colors in palette.json.
Run `python3 build.py` after editing this palette; only files in this directory change.
Derived readable tones are documented in derived.json and contrast.json.

Apply: `symphony switch dreamcore`
Return: `symphony switch zen`
Browser chrome follows the selected theme on the next normal browser restart.
Official Spotify uses Spicetify with .config/spicetify/Themes/symphony/user.css.in.
Its static CSS is generated from the same palette. Super+M opens official Spotify.
Spotify Qt follows the selected theme on app restart (launch it from Rofi).
Its static QSS is generated from the same palette by .config/spotify-qt/build-style.py.
No webpage styles, account data, monitor color controls or extra background processes.

Wallpaper originals: ~/Wallpapers/Dreamcore
Selected upscaled copies: ~/Wallpapers/Dreamcore/enhanced-4k
All active wallpapers are 3840x2160 PNG.
Next/previous: Super+Alt+Right/Left; picker: Super+Alt+Up.
Rebuild image copies with upscale-wallpapers.py (local Real-ESRGAN; no automatic downloads).
Previous wallpaper sets are archived in ~/.local/state/dreamcore/backups.
