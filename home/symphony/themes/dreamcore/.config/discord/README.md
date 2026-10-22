# Discord Dreamcore

The official Discord client uses Vencord, installed with the official CLI
installer v1.4.2. The GitHub release asset's SHA-256 was verified before use.
The installation lives in ~/.config/discord; no system packages or root-owned
files were patched. The original app.asar is retained as resources/_app.asar and
has a separate backup under ~/.local/state/discord-dreamcore.

The enabled local theme is **Dreamcore**, listed under Discord settings →
Vencord → Themes. It has blue #194B66 surfaces, cream #FAEEBA text, pastel brand
controls, subtle hover/selection colors and readable feedback/status colors.
Native layout, messages, avatars, media, call controls and keyboard shortcuts
are preserved. No remote CSS imports, animated backgrounds or blur are added.
Vencord's standard required plugins and default CrashHandler remain; no optional
feature plugins were enabled for this theme.

## Files and shared palette

- variables.css.in maps the shared palette.json and derived.json to Discord tokens.
- variables.css is generated from that template.
- surfaces.css styles structural panels, menus, input and code backgrounds.
- controls.css contains small hover transitions and brand control colors.
- dreamcore.theme.css is the generated distribution file with theme metadata.

The theme's build.py generates the variable and distribution files. It also
builds other rice components, so for a Discord-only edit regenerate only these
outputs or edit surfaces.css/controls.css and rebuild their combined theme.

~/.config/Vencord/themes/dreamcore.theme.css links to the generated theme.
Symphony's 35-vencord-dreamcore.sh hook updates the link when switching rice:
Dreamcore supplies its colors, other themes use inactive.css and retain native
Discord colors. Vencord reloads the theme when that directory link changes.
After regenerating theme files while Discord is running, run the hook with
CURRENT_LINK pointing to ~/.config/symphony/current, or reload Discord.
The original Zen directory remains untouched.

## Recovery

Disable Dreamcore under Vencord → Themes to return to native Discord colors.
For a temporary launch without Vencord, the installed patcher supports
`discord --vanilla`. To remove Vencord, use the same official installer with
--uninstall and --location ~/.config/discord. After a Discord update, use Repair
in the installer if Vencord no longer loads. Vencord's own update defaults remain.

Installer, private backups and verification: ~/.local/state/discord-dreamcore.
Theme sources contain no account credentials, cookies, tokens or messages.
