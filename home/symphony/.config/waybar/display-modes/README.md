# Waybar display modes

Super + Shift + B opens a Rofi menu with three text rows, without icons:
`Islands`, `Full-width bar`, and `Hide Waybar`.
The current mode is selected initially; Escape cancels without changing the
panel. Choosing either visible mode shows Waybar on both monitors; hiding it
keeps the last selected geometry for the next start.
It also appears in the Super + Space launcher as `Waybar Appearance`.
Super + Shift + Space keeps its existing show/hide action.

Commands:

```sh
~/.config/waybar/display-mode toggle
~/.config/waybar/display-mode islands
~/.config/waybar/display-mode strip
~/.config/waybar/display-mode status
~/.local/bin/waybar-mode-menu
```

The selection is saved in ~/.local/state/waybar-display/mode. The service's
zz-display-mode.conf runs the existing Lua-compatible Waybar binary through
display-mode. It generates a runtime config from the current config.jsonc and
imports the current theme's CSS. The strip override changes only panel geometry
and uses colors.css for its background. Theme sources and module settings remain
untouched. If Waybar is hidden, a mode change takes effect on its next start.

The source config can contain JSONC comments and trailing commas; no extra
packages are needed to generate the runtime config.

To remove this feature, remove the waybar-display-mode block from Hyprland's
local.lua and the service's zz-display-mode.conf, then reload Hyprland and run
systemctl --user daemon-reload followed by restarting symphony-waybar.service.
