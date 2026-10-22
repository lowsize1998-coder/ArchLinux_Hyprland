# Codex · Dreamcore

`dreamcore.tmTheme` is the Codex CLI syntax theme. It is linked from
`~/.codex/themes/dreamcore.tmTheme`; `~/.codex/config.toml` selects `dreamcore`.
The already-running chat can switch without restarting: `/theme` → `dreamcore`.

Colors come from Symphony Dreamcore `palette.json` and `derived.json`.
Keywords, functions, types and numbers retain the user's explicit orange accent
`#F59127`. Readable derived colors are used for comments and deleted lines.
The theme file contains snapshots of these colors; regenerate it when changing
those palette roles. Ghostty supplies the overall canvas and ANSI UI colors.

The previous `myvault-zen.tmTheme` and Symphony Zen files are preserved.
To switch syntax back, select `/theme` → `zenburn` (previous active theme)
or `myvault-zen` (existing custom theme).
