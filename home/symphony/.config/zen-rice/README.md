# Symphony Zen Browser

Installed configuration for Zen 1.23b / Gecko 157 on Arch + Hyprland.

## Files

```text
~/.config/zen-rice → ~/symphony/.config/zen-rice
├── chrome/
│   ├── userChrome.css      imports the interface modules
│   ├── userContent.css     styles only named internal about: pages
│   ├── colors.css          generated from Symphony GTK colors
│   ├── variables.css       fonts, dimensions, native theme variables
│   ├── sidebar.css
│   ├── tabs.css
│   ├── toolbar.css
│   ├── urlbar.css
│   ├── menus.css
│   └── panels.css
├── preferences.json        only managed configuration, no profile data
└── scripts/
    ├── build-colors.py
    └── rollback.py
```

The active profile's `chrome/` contains symlinks to these files.
The original Zen-generated `zen-themes.css` is preserved.
No `user.js` hardening pack is installed.

## Design and performance

Colors come from `~/.config/symphony/current/.config/gtk-3.0/colors.css`.
Hover/selection colors are computed when the palette changes. There is no
polling process, remote CSS import, continuous animation or added blur filter.
UI typography: JetBrainsMono Nerd Font 14 px; native SVG icons are preserved.
Ordinary websites retain their own CSS. Defaults use Noto Sans / Noto Serif
and JetBrainsMono for monospace; emoji fallback remains Noto Color Emoji.

The sidebar supports the normal expanded view and the user's collapse toggle; the URL bar uses the full top toolbar,
workspace animation is 120 ms, and compact-sidebar width animation is disabled.
Zen's installed defaults already restore pinned tabs on demand; that behavior is preserved.
Hardware rendering remains enabled. No browser frame-rate cap is configured.

## Navigation

- Workspaces: General, Development, Study, Media.
- Essentials: GitHub and ChatGPT, created as lazy/pending tabs.
- Development pin: Go Packages; Study pin: Arch Wiki. Both start pending.
- Search keywords: `gh` GitHub, `aw` Arch Wiki, `pkg` Go packages.
- Four development bookmarks are grouped in `Development · Symphony`.
- Existing user tabs, bookmarks and shortcuts are preserved.
- Super+B uses the Zen launcher; the existing browser-default associations remain.

## Palette updates

```bash
python3 ~/.config/zen-rice/scripts/build-colors.py
```

The hook `~/symphony/install/themes/hooks/60-zen-rice.sh` regenerates colors on
Symphony theme changes. Browser CSS picks up the new palette on the next
normal Zen restart. The hook never closes browser windows automatically.
Changing CSS modules also requires a normal restart outside the diagnostic session.

## Backup and rollback

Initial closed-profile backup is local, outside Git, with directory mode 700:
`~/.local/state/zen-rice/backups/20261006-110241-full-profile`.
Original managed preference values and created navigation metadata are also
stored under `~/.local/state/zen-rice/`, outside the reusable configuration directory.

Validate rollback without changes:

```bash
python3 ~/.config/zen-rice/scripts/rollback.py --check
```

To roll back styling and managed preferences, first close Zen normally, then:

```bash
python3 ~/.config/zen-rice/scripts/rollback.py
```

The script preserves user tabs, workspaces, bookmarks and credentials. Later
changes to preference values are preserved; modified CSS links require review.
Restoring a complete profile is a separate operation requiring an explicit request.

## Zen Mods assessment

Five candidates were reviewed from the official Zen theme store:

| Mod | CSS size / lines | Relevant cost or overlap | Decision |
|---|---:|---|---|
| Better Find Bar | 4,915 bytes / 197 | Optional backdrop blur, 0.35 s movement; can hide useful controls | Native find bar themed directly |
| Super Sleek UI | 2,719 bytes / 108 | Backdrop blur and opinionated layout changes | Own native layout used |
| SuperPins | 24,092 bytes / 851 | Large rule set for pinned/essential behavior already provided by Zen | Native pins retained |
| Transparent Zen | 13,138 bytes / 479 | Filters, backdrop blur, broad transitions | Opaque UI chosen for predictability |
| Zen Context Menu | 27,539 bytes / 844 | Many visibility/permission rules that can hide useful actions | Native actions preserved and menus themed |

These are code-level cost indicators, not measured performance numbers for
the mods. None of the candidates was installed. The current user-requested
setup uses no additional extensions or runtime theme daemon.

## Validation limits

Native Wayland and WebRender were confirmed in the running browser. The local
HTTP test verified ordinary website styling and JavaScript interaction.
The portal services, PipeWire and WirePlumber are active; screen/window sharing
capabilities are exposed. Actual screen sharing and account authentication
still need user-driven checks.

NVIDIA VA-API initialization succeeds on the host, but the browser rejects
hardware decoding with `FEATURE_FAILURE_VIDEO_DECODING_TEST_FAILED`.
A temporary forced-decode test with the RDD sandbox intact did not establish
NVDEC use; that override was reverted. Renderer acceleration is unaffected.
The RDD sandbox was never disabled. NVIDIA/kernel/system-wide settings were not changed.

## Git

Only this configuration and the Symphony hook are suitable for Git.
Do not add `.config/zen`, profiles, local state/backups, cookies, passwords,
sessions, history, caches or diagnostic screenshots. No Git commit was created.
The current Symphony directory has no Git repository; no repository was initialized.
