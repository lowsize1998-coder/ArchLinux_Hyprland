#!/usr/bin/env python3
"""Build an independent theme from the fourteen user-selected source colors.

Only writes inside this theme directory. No browser data or other theme inputs.
"""
import json
import re
import struct
import subprocess
import zlib
from pathlib import Path
from string import Template
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parent
C = json.loads((ROOT / 'palette.json').read_text())
assert len(C) == 15 and all(re.fullmatch(r'#[0-9A-Fa-f]{6}', v) for k, v in C.items() if k != 'name')


def rgb(c):
    return tuple(int(c[i:i+2], 16) for i in (1, 3, 5))


def mix(a, b, weight):
    return '#' + ''.join(f'{round(x*(1-weight)+y*weight):02X}' for x, y in zip(rgb(a), rgb(b)))


def luminance(c):
    def linear(v):
        v /= 255
        return v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4
    return sum(w*linear(v) for w, v in zip((.2126, .7152, .0722), rgb(c)))


def contrast(a, b):
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi+.05)/(lo+.05)


def readable(color, surface):
    """Derive the smallest white/black mix that reaches 4.5:1 on this surface."""
    target = '#FFFFFF' if luminance(surface) < .18 else '#000000'
    for n in range(101):
        value = mix(color, target, n/100)
        if contrast(value, surface) >= 4.5:
            return value
    raise ValueError('Cannot produce readable color')


def write(name, text):
    p = ROOT/name
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists() or p.read_text() != text:
        p.write_text(text.rstrip()+'\n')


def png(color, w=64, h=64):
    def chunk(tag, data):
        return struct.pack('>I', len(data))+tag+data+struct.pack('>I', zlib.crc32(tag+data)&0xffffffff)
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR', struct.pack('>2I5B',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress((b'\x00'+bytes(rgb(color))*w)*h))+chunk(b'IEND',b'')


B, P, M, F, S = (C[x] for x in ('background','panel','popup','text','selection'))
I = mix(C['dim_text'], '#000000', .35)
A, T, E, W = (C[x] for x in ('accent','secondary_accent','error','warning'))
I = readable(I, A)
read = {key: readable(C[key], B) for key in ('dim_text','accent','secondary_accent','info','success','warning','error')}
dark_muted = readable(C['dim_text'], P)
dark_link = readable(B, P)
derived = {'ink': I, 'muted_on_light': dark_muted, 'link_on_light': dark_link, **{k+'_on_blue': v for k,v in read.items()}}
write('derived.json', json.dumps(derived, ensure_ascii=False, indent=2))
pairs = [('Blue / cream',F,B),('Blue / secondary',C['secondary_text'],B),('Pink / ink',I,P),('Green menu / ink',I,M),('Selection / ink',I,S)]
pairs += [(k+' on blue',v,B) for k,v in read.items()]
pairs += [(k+' / ink',I,C[k]) for k in ('accent','secondary_accent','warning','success')]
report = [{'pair': name,'foreground': fg,'background': bg,'ratio':round(contrast(fg,bg),2)} for name,fg,bg in pairs]
assert all(r['ratio'] >= 4.5 for r in report), report
write('contrast.json',json.dumps(report,indent=2))

# ANSI tones are readable on the blue terminal canvas, not arbitrary swatches.
ansi = [read['dim_text'],read['error'],read['success'],read['warning'],C['info'],read['accent'],read['secondary_accent'],F]
bright = [mix(x,'#FFFFFF',.22) for x in ansi]
write('.config/ghostty/theme', '\n'.join([f'background = {B}',f'foreground = {F}',f'cursor-color = {C["border"]}',f'cursor-text = {I}',f'selection-background = {S}',f'selection-foreground = {I}',*[f'palette = {i}={v}' for i,v in enumerate(ansi+bright)]]))
write('.config/kitty/colors.conf','\n'.join([f'background {B}',f'foreground {F}',f'cursor {C["border"]}',f'cursor_text_color {I}',f'selection_background {S}',f'selection_foreground {I}',*[f'color{i} {v}' for i,v in enumerate(ansi+bright)]]))
names=['black','red','green','yellow','blue','magenta','cyan','white']
write('.config/alacritty/colors.toml', f'[colors.primary]\nbackground = "{B}"\nforeground = "{F}"\n[colors.selection]\nbackground = "{S}"\ntext = "{I}"\n'+''.join(f'[colors.{group}]\n'+''.join(f'{n} = "{v}"\n' for n,v in zip(names,values)) for group,values in [('normal',ansi),('bright',bright)]))

# GTK semantic aliases. Light panels deliberately have their own foreground.
gtk = {
    'background':B,'foreground':F,'accent_bg_color':A,'accent_fg_color':I,'accent_color':read['accent'],
    'window_bg_color':B,'window_fg_color':F,'view_bg_color':B,'view_fg_color':F,
    'headerbar_bg_color':P,'headerbar_fg_color':I,'headerbar_backdrop_color':P,'headerbar_shade_color':'alpha(black, 0.10)',
    'sidebar_bg_color':P,'sidebar_fg_color':I,'secondary_sidebar_bg_color':P,'secondary_sidebar_fg_color':I,
    'card_bg_color':P,'card_fg_color':I,'card_shade_color':'alpha(black, 0.08)',
    'popover_bg_color':M,'popover_fg_color':I,'dialog_bg_color':P,'dialog_fg_color':I,
    'theme_bg_color':B,'theme_fg_color':F,'theme_base_color':B,'theme_text_color':F,
    'theme_selected_bg_color':S,'theme_selected_fg_color':I,
    'borders':C['border'],'theme_unfocused_bg_color':B,'theme_unfocused_fg_color':C['secondary_text'],
    'theme_unfocused_base_color':B,'theme_unfocused_text_color':F,
    'theme_unfocused_selected_bg_color':S,'theme_unfocused_selected_fg_color':I,
    'destructive_bg_color':E,'destructive_fg_color':F,'destructive_color':read['error'],
    'error_bg_color':E,'error_fg_color':F,'error_color':read['error'],
    'warning_bg_color':W,'warning_fg_color':I,'warning_color':read['warning'],
    'success_bg_color':C['success'],'success_fg_color':I,'success_color':read['success'],
    'black':I,'bright_black':C['border'],'white':C['secondary_text'],
    'red':E,'green':C['success'],'yellow':W,'blue':B,'magenta':A,'cyan':C['info']
}
css='/* Dreamcore: generated from palette.json. */\n'+''.join(f'@define-color {k} {v};\n' for k,v in gtk.items())
for ver in ('gtk-3.0','gtk-4.0'): write(f'.config/{ver}/colors.css',css)
write('.config/hypr/theme/colors.conf',f'$secondary = rgba({A[1:]}ff)\n$outline_variant = rgba({C["border"][1:]}66)\n$activeBorderColor = rgba({A[1:]}ff)\n$background = rgba({B[1:]}ff)\n$foreground = rgba({F[1:]}ff)')
write('.config/waybar/colors.css',f'@define-color on_background {F};\n@define-color surface_container {B};\n@define-color waybar_accent {A};\n@define-color waybar_accent_fg {I};\n@define-color error {read["error"]};')
write('.config/waybar/style.css',f'''
* {{ font-family: "JetBrainsMono Nerd Font"; font-size: 16px; border: none; border-radius: 0; }}
window#waybar {{ background: {B}; color: {F}; border-bottom: 1px solid alpha({C['border']}, 0.35); }}
tooltip, menu {{ background: {M}; color: {I}; border: 1px solid {C['border']}; border-radius: 10px; padding: 8px; }}
tooltip label, menuitem {{ color: {I}; }}
menuitem:hover {{ background: {S}; }}
#workspaces button {{ background: transparent; color: {C['secondary_text']}; padding: 0 8px; margin: 1px 2px; border-radius: 7px; }}
#workspaces button.active, #workspaces button.visible.hosting-monitor {{ background: {S}; color: {I}; font-weight: bold; }}
#workspaces button:hover {{ background: {P}; color: {I}; box-shadow: none; }}
#workspaces button.empty {{ color: {read['dim_text']}; }}
#clock, #mpris, #tray, #pulseaudio, #bluetooth, #backlight, #memory,
#custom-logo, #custom-expand, #custom-idle-indicator, #custom-screenrecording-indicator,
#custom-keyboard-layout, #custom-uair {{ padding: 0 8px; color: {F}; background: transparent; }}
#custom-uair {{ margin: 1px 4px; background: {P}; color: {I}; border-radius: 7px; padding: 0 10px; }}
#custom-uair.paused {{ background: {S}; }}
#custom-screenrecording-indicator.active {{ color: {read['error']}; }}
#clock {{ font-weight: bold; }}

/* Three islands, using the existing Dreamcore palette. */
* {{ min-height: 0; }}
window#waybar {{ background: transparent; border: none; }}
.modules-left, .modules-center, .modules-right {{
    background: {B};
    border: 1px solid alpha({C['border']}, 0.35);
    border-radius: 10px;
    padding: 0 8px;
    min-height: 32px;
}}
#custom-music-icon {{ color: {F}; padding: 0 4px 0 2px; }}
#custom-expand {{ border-radius: 7px; }}
#custom-expand:hover {{ background: {P}; color: {I}; }}
''')
write('.config/rofi/colors.rasi',f'* {{ background: {M}; foreground: {I}; selected: {S}; accent: {A}; }}')
write('.config/rofi/config.rasi',f'''
configuration {{
    modes: "drun";
    show-icons: true;
    icon-theme: "Papirus";
    display-drun: "";
    drun-display-format: "{{name}}";
    terminal: "ghostty";
    font: "JetBrainsMono Nerd Font 12";
}}
* {{ background-color: transparent; text-color: {I}; selected: {S}; }}
window {{ location: center; anchor: center; width: 480px; background-color: {M}; border: 2px; border-color: {C['border']}; border-radius: 14px; }}
mainbox {{ padding: 16px; spacing: 12px; children: [ "inputbar", "listview" ]; }}
inputbar {{ padding: 12px; background-color: {P}; border-radius: 8px; children: [ "entry" ]; }}
entry {{ placeholder: "Поиск"; placeholder-color: {dark_muted}; text-color: {I}; }}
listview {{ lines: 7; columns: 1; spacing: 5px; fixed-height: true; scrollbar: false; }}
element {{ padding: 10px; spacing: 12px; border-radius: 8px; }}
element normal.normal, element normal.active, element normal.urgent,
element alternate.normal, element alternate.active, element alternate.urgent {{
    background-color: transparent;
    text-color: {I};
}}
element selected.normal, element selected.active, element selected.urgent {{
    background-color: {S};
    text-color: {I};
}}
element-icon {{ size: 28px; }}
element-text {{ vertical-align: 0.5; text-color: inherit; }}
''')
write('.config/swaync/style.css',f'''
* {{ font-family: "Noto Sans"; font-size: 14px; }}
.control-center {{ background: {M}; color: {I}; border: 1px solid {C['border']}; border-radius: 14px; padding: 12px; }}
.notification-row {{ outline: none; }}
.notification {{ background: {P}; color: {I}; border: 1px solid {C['border']}; border-radius: 10px; padding: 10px; margin: 5px; box-shadow: none; }}
.notification-content, .summary, .body, .time, .notification-default-action {{ background: transparent; color: {I}; }}
.notification-action, .close-button, .widget-title button, .widget-dnd {{ background: {S}; color: {I}; border: none; border-radius: 7px; padding: 6px; }}
.notification-action:hover, .close-button:hover, .widget-title button:hover {{ background: {A}; color: {I}; }}
.widget-mpris {{ background: {P}; color: {I}; border-radius: 10px; padding: 10px; margin: 8px 0; }}
.widget-mpris-player {{ background: {P}; color: {I}; border-radius: 8px; }}
.widget-title, .widget-title label, .widget-dnd label, .widget-mpris-title, .widget-mpris-subtitle, .notification-group-headers {{ color: {I}; }}
.widget-dnd switch {{ background: {P}; border: none; }}
.widget-dnd switch:checked {{ background: {A}; }}
.widget-dnd switch slider {{ background: {S}; }}
.notification.critical {{ border: 2px solid {E}; }}
''')
# Each launcher retains its existing script/actions; only its stylesheet changes.
for kind in ('search','clipboard','emoji','keybinds','powermenu','power-profiles','rofi-Beats','rofi-Beats-menu','theme-picker','wallpaper'):
    text=(ROOT/'.config/rofi/config.rasi').read_text()
    if kind in ('theme-picker','wallpaper'):
        text+='\nwindow { width: 80%; }\nlistview { lines: 2; columns: 5; }\nelement { orientation: vertical; }\nelement-icon { size: 160px; horizontal-align: 0.5; }\nelement-text { horizontal-align: 0.5; }\n'
    if kind=='keybinds': text+='\nwindow { width: 75%; }\nlistview { lines: 14; }\n'
    write(f'.config/rofi/custom-rofi/config-{kind}.rasi',text)
write('.config/swayosd/style.css',f'''
window {{ background: {P}; color: {I}; border: 1px solid {C['border']}; border-radius: 12px; padding: 12px; }}
#container {{ margin: 12px; }}
image, label {{ color: {I}; }}
progressbar {{ min-height: 6px; }}
trough {{ background: {S}; border: none; border-radius: 6px; }}
progress {{ background: {A}; border: none; border-radius: 6px; }}
''')
write('.config/hypr/hyprlock.conf',f'''
# Dreamcore lock screen. Authentication behavior stays native.
background {{
    monitor =
    color = rgba({B[1:]}ff)
}}
input-field {{
    monitor =
    size = 260, 48
    outline_thickness = 2
    inner_color = rgba({P[1:]}ff)
    outer_color = rgba({C['border'][1:]}ff)
    font_color = rgba({I[1:]}ff)
    check_color = rgba({A[1:]}ff)
    fail_color = rgba({E[1:]}ff)
    placeholder_text = <i>Пароль</i>
    fail_text = <b>Повторите ввод ($ATTEMPTS)</b>
    rounding = 10
    position = 0, -40
    halign = center
    valign = center
}}
label {{
    monitor =
    text = $TIME
    color = rgba({F[1:]}ff)
    font_size = 64
    font_family = JetBrainsMono Nerd Font
    position = 0, 180
    halign = center
    valign = center
}}
auth {{
    fingerprint:enabled = false
}}
''')

# Qt palette is a per-user Fusion palette; the previous config is restored.
qt = [F,P,C['border'],S,dark_muted,C['dim_text'],F,F,I,B,B,I,S,I,C['info'],read['accent'],mix(B,F,.08),B,M,I,read['dim_text']]
write('.config/qt6ct/colors.conf','[ColorScheme]\n'+''.join(k+'='+', '.join('#ff'+v[1:].lower() for v in qt)+'\n' for k in ('active_colors','inactive_colors','disabled_colors')))
write('.config/qt6ct/qt6ct.conf',f'[Appearance]\nicon_theme=Papirus\nstyle=Fusion\ncustom_palette=true\ncolor_scheme_path={ROOT}/.config/qt6ct/colors.conf\n')

write('.config/yazi/theme.toml',f'''
[mgr]
cwd = {{ fg = "{read['info']}" }}
hovered = {{ fg = "{I}", bg = "{P}", bold = true }}
preview_hovered = {{ fg = "{I}", bg = "{S}" }}
find_keyword = {{ fg = "{I}", bg = "{W}", bold = true }}
find_position = {{ fg = "{read['info']}", bold = true }}
border_symbol = "│"
border_style = {{ fg = "{C['border']}" }}
marker_selected = {{ fg = "{C['success']}", bg = "{C['success']}" }}
marker_copied = {{ fg = "{T}", bg = "{T}" }}
marker_cut = {{ fg = "{read['error']}", bg = "{read['error']}" }}
[mode]
normal_main = {{ fg = "{I}", bg = "{A}", bold = true }}
normal_alt = {{ fg = "{I}", bg = "{P}" }}
select_main = {{ fg = "{I}", bg = "{S}", bold = true }}
select_alt = {{ fg = "{I}", bg = "{P}" }}
unset_main = {{ fg = "{I}", bg = "{W}", bold = true }}
unset_alt = {{ fg = "{I}", bg = "{P}" }}
[status]
overall = {{ fg = "{I}", bg = "{P}" }}
perm_type = {{ fg = "{B}" }}
perm_read = {{ fg = "{I}" }}
perm_write = {{ fg = "{E}" }}
perm_exec = {{ fg = "{I}" }}
perm_sep = {{ fg = "{dark_muted}" }}
[input]
border = {{ fg = "{C['border']}" }}
title = {{ fg = "{F}" }}
value = {{ fg = "{F}" }}
selected = {{ fg = "{I}", bg = "{S}" }}
[select]
border = {{ fg = "{C['border']}" }}
active = {{ fg = "{I}", bg = "{S}" }}
inactive = {{ fg = "{F}" }}
[tasks]
border = {{ fg = "{C['border']}" }}
title = {{ fg = "{F}" }}
hovered = {{ fg = "{I}", bg = "{P}" }}
[which]
mask = {{ bg = "{M}" }}
cand = {{ fg = "{I}" }}
rest = {{ fg = "{I}" }}
desc = {{ fg = "{I}" }}
separator = " → "
separator_style = {{ fg = "{I}" }}
[help]
on = {{ fg = "{F}" }}
run = {{ fg = "{read['info']}" }}
desc = {{ fg = "{C['secondary_text']}" }}
hovered = {{ fg = "{I}", bg = "{S}", bold = true }}
footer = {{ fg = "{I}", bg = "{P}" }}
[filetype]
rules = [
  {{ url = "*/", fg = "{read['info']}" }},
  {{ url = "*", fg = "{F}" }}
]
''')
btop={'main_bg':B,'main_fg':F,'title':F,'hi_fg':read['accent'],'selected_bg':S,'selected_fg':I,'inactive_fg':read['dim_text'],'proc_misc':C['info']}
btop.update({k:C['border'] for k in ('cpu_box','mem_box','net_box','proc_box','div_line')})
for prefix in ('temp','cpu','free','cached','available','used','download','upload'):
    for suffix,c in zip(('start','mid','end'),(T,C['info'],read['error'])): btop[prefix+'_'+suffix]=c
write('.config/btop/themes/current.theme','\n'.join(f'theme[{k}]="{v}"' for k,v in btop.items()))
write('.config/starship.toml',f'''format = "$directory$git_branch$git_status$character"
[directory]
style = "{C['info']}"
truncation_length = 3
[git_branch]
style = "{read['accent']}"
[git_status]
style = "{read['warning']}"
[character]
success_symbol = "[❯]({C['success']})"
error_symbol = "[❯]({read['error']})"
''')
# The native rmpc defaults supply its version-specific structural schema.
default=subprocess.run(['rmpc','theme'],check=True,text=True,capture_output=True).stdout
for key,c in [('background_color',B),('text_color',F),('header_background_color',P),('modal_background_color',M)]:
    default=default.replace(f'{key}: None,',f'{key}: "{c}",')
named={'blue':read['accent'],'black':I,'white':F,'yellow':read['warning'],'red':read['error'],'light_green':C['success'],'magenta':read['accent']}
default=re.sub(r'(fg|bg): "([a-z_]+)"',lambda m:f'{m[1]}: "{named.get(m[2],m[2])}"',default)
# Explicitly color text that lives on the light header and popup surfaces.
default=default.replace('inactive_style: (),',f'inactive_style: (fg: "{I}"),')
default=default.replace('label_style: (),',f'label_style: (fg: "{I}"),')
# A blue header avoids per-label bright default colors losing contrast on pink.
default=default.replace(f'header_background_color: "{P}"',f'header_background_color: "{B}"')
default=default.replace(f'modal_background_color: "{M}"',f'modal_background_color: "{B}"')
default=default.replace('"green"',f'"{C["success"]}"')
write('.config/rmpc/themes/current.ron',default)

# Independent modular browser chrome. Absolute imports avoid the profile's old modules.
chrome='.config/zen-browser/chrome/'
base=(ROOT/chrome).as_uri()
tokens={'bg':B,'panel':P,'popup':M,'fg':F,'ink':I,'muted':C['secondary_text'],'light-muted':dark_muted,'selection':S,'accent':A,'border':C['border'],'info':C['info'],'error':E}
write(chrome+'colors.css',':root {\n'+''.join(f'  --dream-{k}: {v};\n' for k,v in tokens.items())+'}\n')
write(chrome+'variables.css','''
@-moz-document url("chrome://browser/content/browser.xhtml") {
  :root {
    --zen-primary-color: var(--dream-accent) !important;
    --zen-colors-primary: var(--dream-bg) !important;
    --zen-colors-secondary: var(--dream-panel) !important;
    --zen-colors-tertiary: var(--dream-selection) !important;
    --zen-colors-border: var(--dream-border) !important;
    --zen-main-browser-background: var(--dream-bg) !important;
    --zen-main-browser-background-toolbar: var(--dream-panel) !important;
    --zen-themed-toolbar-bg-transparent: var(--dream-panel) !important;
    --zen-border-radius: 10px !important;
    --zen-element-separation: 6px !important;
    --zen-active-tab-scale: 1 !important;
    --toolbar-bgcolor: var(--dream-panel) !important;
    --toolbar-color: var(--dream-ink) !important;
    --toolbox-textcolor: var(--dream-ink) !important;
    --toolbox-textcolor-inactive: var(--dream-ink) !important;
    --zen-sidebar-themed-icon-fill: var(--dream-ink) !important;
    --zen-colors-primary-foreground: var(--dream-ink) !important;
    --zen-colors-input-bg: var(--dream-panel) !important;
    --zen-toolbar-element-bg: var(--dream-panel) !important;
    --zen-toolbar-element-bg-hover: var(--dream-selection) !important;
    --zen-accent-button-background: var(--dream-selection) !important;
    --zen-accent-button-color: var(--dream-ink) !important;
    --toolbarbutton-background-color-hover: var(--dream-selection) !important;
    --toolbarbutton-background-color-active: var(--dream-selection) !important;
    --toolbarbutton-icon-fill: var(--dream-ink) !important;
    --toolbarbutton-hover-background: var(--dream-selection) !important;
    --toolbarbutton-active-background: var(--dream-selection) !important;
    --toolbar-field-background-color: var(--dream-panel) !important;
    --toolbar-field-color: var(--dream-ink) !important;
    --toolbar-field-focus-background-color: var(--dream-panel) !important;
    --toolbar-field-focus-color: var(--dream-ink) !important;
    --arrowpanel-background: var(--dream-popup) !important;
    --arrowpanel-color: var(--dream-ink) !important;
    --arrowpanel-border-color: var(--dream-border) !important;
    --lwt-text-color: var(--dream-ink) !important;
    --tab-selected-bgcolor: var(--dream-selection) !important;
    --tab-selected-textcolor: var(--dream-ink) !important;
  }
  #main-window { font-family: "JetBrainsMono Nerd Font", "Noto Sans", sans-serif !important; font-size: 14px !important; color: var(--dream-ink) !important; }
  #zen-main-app-wrapper, #zen-browser-background { background: var(--dream-bg) !important; }
}
''')
write(chrome+'sidebar.css','''
@-moz-document url("chrome://browser/content/browser.xhtml") {
  #navigator-toolbox, #titlebar, #TabsToolbar, #zen-sidebar-top-buttons, #zen-sidebar-bottom-buttons, #zen-sidebar-icons-wrapper {
    background: var(--dream-panel) !important; color: var(--dream-ink) !important;
  }
  .tabbrowser-tab { color: var(--dream-ink) !important; }
  .tab-background { background: transparent !important; border-radius: 8px !important; }
  .tabbrowser-tab:hover .tab-background { background: var(--dream-selection) !important; }
  .tabbrowser-tab[selected] .tab-background { background: var(--dream-selection) !important; border: 1px solid var(--dream-accent) !important; }
  #zen-sidebar-icons-wrapper toolbarbutton { fill: var(--dream-ink) !important; color: var(--dream-ink) !important; }
  #navigator-toolbox, zen-workspace {
    --toolbox-textcolor: var(--dream-ink) !important;
    --toolbar-color: var(--dream-ink) !important;
    color: var(--dream-ink) !important;
    color-scheme: light !important;
  }
  #navigator-toolbox toolbarbutton, .zen-current-workspace-indicator-name,
  .zen-current-workspace-indicator-icon, .zen-workspace-sidebar-name,
  .zen-workspace-sidebar-icon, #zen-workspaces-button {
    color: var(--dream-ink) !important;
    fill: var(--dream-ink) !important;
  }
  .zen-current-workspace-indicator-name { opacity: 1 !important; }
  #zen-workspaces-button toolbarbutton { --zen-sidebar-themed-icon-fill: var(--dream-ink) !important; }
}
''')
write(chrome+'toolbar.css','''
@-moz-document url("chrome://browser/content/browser.xhtml") {
  #nav-bar, #PersonalToolbar, #zen-appcontent-navbar-container { background: var(--dream-panel) !important; color: var(--dream-ink) !important; }
  #urlbar-background, #searchbar { background: var(--dream-panel) !important; border: 1px solid var(--dream-border) !important; border-radius: 8px !important; }
  #urlbar-input, #searchbar input, #urlbar .urlbar-input { color: var(--dream-ink) !important; }
  #urlbar[breakout-extend] #urlbar-background { background: var(--dream-popup) !important; }
  .urlbarView { background: var(--dream-popup) !important; color: var(--dream-ink) !important; }
  .urlbarView-row[selected], .urlbarView-row:hover { background: var(--dream-selection) !important; color: var(--dream-ink) !important; }
  .urlbarView-url, .urlbarView-action { color: var(--dream-bg) !important; }
  /* Gecko 157 / Zen 1.23 uses classes for all omnibox instances. */
  .urlbar {
    --input-color: var(--dream-ink) !important;
    --toolbar-field-color: var(--dream-ink) !important;
    --zen-urlbar-background-base: var(--dream-popup) !important;
    --zen-urlbar-background-transparent: var(--dream-popup) !important;
    color: var(--dream-ink) !important;
    color-scheme: light !important;
  }
  .urlbar .urlbar-background {
    background: var(--dream-panel) !important;
    border: 1px solid var(--dream-border) !important;
    border-radius: 8px !important;
    backdrop-filter: none !important;
  }
  .urlbar[breakout-extend] .urlbar-background {
    background: var(--dream-popup) !important;
    border-radius: 10px !important;
  }
  .urlbar .urlbar-input, .urlbar .urlbar-input::placeholder {
    color: var(--dream-ink) !important;
    -webkit-text-fill-color: var(--dream-ink) !important;
    opacity: 1 !important;
  }
  .urlbar .urlbar-input-container { color: var(--dream-ink) !important; }
  .urlbar .urlbarView { background: var(--dream-popup) !important; color: var(--dream-ink) !important; }
  .urlbar .urlbarView-row[selected], .urlbar .urlbarView-row:hover {
    background: var(--dream-selection) !important; color: var(--dream-ink) !important;
  }
  /* Native Zen gives every descendant of a selected result a white color. */
  .urlbar .urlbarView-title, .urlbar .urlbarView-title *,
  .urlbar .urlbarView-action, .urlbar .urlbarView-title-separator,
  .urlbar .urlbarView-title-separator::before {
    color: var(--dream-ink) !important;
    -webkit-text-fill-color: var(--dream-ink) !important;
  }
  .urlbar .urlbarView-row .urlbarView-favicon {
    color: var(--dream-ink) !important;
    fill: var(--dream-ink) !important;
    stroke: var(--dream-ink) !important;
  }
  findbar { background: var(--dream-panel) !important; color: var(--dream-ink) !important; }
}
''')
write(chrome+'newtab.css','''
@-moz-document url("chrome://browser/content/browser.xhtml") {
  /* Only the browser's empty tab, never a loaded website. */
  :root[zen-has-empty-tab="true"] #tabbrowser-tabpanels,
  :root[zen-has-empty-tab="true"] .browserSidebarContainer,
  :root[zen-has-empty-tab="true"] .browserContainer,
  :root[zen-has-empty-tab="true"] browser[type="content"] {
    background: var(--dream-bg) !important;
  }
}
''')
write(chrome+'menus.css','''
@-moz-document url("chrome://browser/content/browser.xhtml") {
  menupopup, panel, .panel-subview-body { --arrowpanel-background: var(--dream-popup) !important; --arrowpanel-color: var(--dream-ink) !important; }
  menupopup::part(content), panel::part(content) { background: var(--dream-popup) !important; color: var(--dream-ink) !important; border: 1px solid var(--dream-border) !important; border-radius: 10px !important; }
  menu, menuitem, .subviewbutton { color: var(--dream-ink) !important; }
  menuitem[_moz-menuactive], menu[_moz-menuactive], .subviewbutton:hover { background: var(--dream-selection) !important; }
}
''')
write(chrome+'library.css','''
@-moz-document url("chrome://browser/content/browser.xhtml") {
  /* The Library overlays a dark surface and needs the terminal foreground. */
  zen-library {
    --toolbar-color: var(--dream-fg) !important;
    --toolbox-textcolor: var(--dream-fg) !important;
    --toolbox-textcolor-inactive: var(--dream-fg) !important;
    --toolbarbutton-icon-fill: var(--dream-fg) !important;
    --zen-sidebar-themed-icon-fill: var(--dream-fg) !important;
    --zen-accent-button-color: var(--dream-fg) !important;
    --toolbar-color-scheme: dark !important;
    color: var(--dream-fg) !important;
    color-scheme: dark !important;
  }
  zen-library .zen-library-tab,
  zen-library .zen-library-tab label,
  zen-library .zen-library-row-title,
  zen-library .zen-library-row-subtitle,
  zen-library .zen-library-search-header input,
  zen-library .zen-library-search-header input::placeholder,
  zen-library .zen-library-filter-header,
  zen-library .zen-library-group-label,
  zen-library .zen-library-section-empty {
    color: var(--dream-fg) !important;
  }
  zen-library .zen-library-tab-icon-image {
    --stroke: var(--dream-fg) !important;
    --fill: var(--dream-fg) !important;
    stroke: var(--dream-fg) !important;
  }
  zen-library .zen-library-row-icon {
    color: var(--dream-fg) !important;
    fill: var(--dream-fg) !important;
  }
}
''')
write(chrome+'userChrome.css','/* Independent Dreamcore chrome. No imports from other themes. */\n'+''.join(f'@import url("{base}/{name}.css");\n' for name in ('colors','variables','sidebar','toolbar','newtab','menus','library','dark-chrome')))
write(chrome+'userContent.css',f'''@-moz-document url("about:newtab"), url("about:home"), url("about:preferences"), url("about:downloads"), url("about:blank"), url("chrome://browser/content/blanktab.html") {{
  :root {{ --in-content-page-background: {B} !important; --in-content-page-color: {F} !important; --in-content-box-background: {B} !important; --in-content-primary-button-background: {S} !important; --in-content-primary-button-text-color: {I} !important; --in-content-link-color: {C['info']} !important; color-scheme: dark; }}
  html, body {{ background: {B} !important; color: {F} !important; }}
}}''')

z={'default-bg':B,'default-fg':F,'statusbar-bg':P,'statusbar-fg':I,'inputbar-bg':P,'inputbar-fg':I,'completion-bg':M,'completion-fg':I,'completion-group-bg':M,'completion-group-fg':I,'completion-highlight-bg':S,'completion-highlight-fg':I,'notification-bg':P,'notification-fg':I,'notification-error-bg':E,'notification-error-fg':F,'notification-warning-bg':W,'notification-warning-fg':I,'index-bg':M,'index-fg':I,'index-active-bg':S,'index-active-fg':I,'render-loading-bg':B,'render-loading-fg':F,'highlight-color':A+'60','highlight-active-color':A+'A0','highlight-fg':I}
write('.config/zathura/appearance','\n'.join(f'set {k} "{v}"' for k,v in z.items()))
write('.config/zathura/profiles/rice',f'set recolor-darkcolor "{F}"\nset recolor-lightcolor "{B}"\nset recolor-keephue true\nset recolor-reverse-video true\nset recolor true')
write('.config/zathura/profiles/default',(ROOT/'.config/zathura/profiles/rice').read_text())

# Minimal native Spotify color replacement, without theme JS or extensions.
sp={'text':F,'subtext':C['secondary_text'],'main':B,'sidebar':B,'player':B,'card':B,'shadow':I,'selected-row':B,'button':B,'button-active':B,'button-disabled':T,'tab-active':B,'notification':B,'notification-error':E,'misc':C['border']}
write('.config/spicetify/Themes/symphony/color.ini','[base]\n'+''.join(f'{k} = {v[1:]}\n' for k,v in sp.items()))
spotify_template = ROOT / '.config/spicetify/Themes/symphony/user.css.in'
write('.config/spicetify/Themes/symphony/user.css', Template(spotify_template.read_text()).substitute({**C, **derived}))
write('.config/vesktop/themes/symphony-discord.css',f'''
/* Native CSS tokens only; no remote theme framework. */
.theme-dark {{ --background-primary: {B}; --background-secondary: {B}; --background-tertiary: {B}; --background-floating: {M}; --text-normal: {F}; --text-muted: {C['secondary_text']}; --header-primary: {F}; --interactive-normal: {F}; --brand-experiment: {A}; }}
''')
discord_colors = {**C, **derived, 'hover_color': mix(B, T, .12), 'selected_color': mix(B, A, .18), 'border_color': mix(B, C['border'], .35)}
write('.config/discord/variables.css', Template((ROOT / '.config/discord/variables.css.in').read_text()).substitute(discord_colors))
discord_meta = '/**\n * @name Dreamcore\n * @author rozetta\n * @version 1.0.0\n * @description Shared Dreamcore palette, blue surfaces and pastel accents.\n */\n'
write('.config/discord/dreamcore.theme.css', discord_meta + '\n'.join((ROOT / '.config/discord' / name).read_text() for name in ('variables.css', 'surfaces.css', 'controls.css')))
(ROOT/'backgrounds').mkdir(exist_ok=True)
(ROOT/'assets').mkdir(exist_ok=True)
(ROOT/'assets/solid-blue.png').write_bytes(png(B))
if not any(p.suffix.lower() in ('.png','.jpg','.jpeg','.webp') for p in (ROOT/'backgrounds').iterdir()):
    (ROOT/'backgrounds/1.png').write_bytes(png(B))
# Native Telegram package: explicit palette values, no account data or local theme.
schema=ROOT/'upstream/telegram-keynames.json'
if schema.exists():
    keys=json.loads(schema.read_text())
    values={}
    for index,key in enumerate(keys):
        name=key.lower()
        if name.startswith(('historytext','historylink','historyfile','historyicon')) or name.startswith(('msgin','msgout')):
            value=I
            if 'bg' in name: value=S if ('out' in name or 'selected' in name) else P
            if 'link' in name: value=B
        elif 'bg' in name:
            value=P
            if any(t in name for t in ('active','selected','over','ripple')): value=S
            if 'menu' in name or 'emoji' in name: value=M
            if 'error' in name or 'attention' in name: value=E
            if 'shadow' in name or 'fade' in name: value=I+'30'
        else:
            value=I
            if any(t in name for t in ('link','online','active')): value=B
            if 'error' in name or 'attention' in name: value=E
            if 'shadow' in name or 'fade' in name: value=I+'30'
        if name.startswith(('peer','historypeer','avatar')):
            value=(A,T,C['info'],C['success'],W,C['error'])[index%6]
        values[key]=value
    values.update(windowBg=P,windowFg=I,windowBgActive=S,windowFgActive=I,menuBg=M,menuFg=I,
                  dialogsBg=P,dialogsBgActive=S,dialogsNameFg=I,dialogsNameFgActive=I,
                  activeButtonBg=A,activeButtonBgOver=S,activeButtonFg=I,
                  msgInBg=P,msgOutBg=S,historyTextInFg=I,historyTextOutFg=I,
                  historyTextInFgSelected=I,historyTextOutFgSelected=I)
    assert all(re.fullmatch(r'#[0-9a-fA-F]{6}(?:[0-9a-fA-F]{2})?',value) for value in values.values())
    body='// Independent Dreamcore palette. Public native Telegram key schema.\n'+''.join(f'{key}: {value};\n' for key,value in values.items())
    write('.config/telegram/dreamcore.tdesktop-palette',body)
    with ZipFile(ROOT/'.config/telegram/dreamcore.tdesktop-theme','w',ZIP_DEFLATED) as archive:
        archive.writestr('colors.tdesktop-theme',body)
        archive.writestr('background.png',png(B))
wall=ROOT/'wallpaper'
if not wall.is_symlink():
    files=sorted((ROOT/'backgrounds').iterdir())
    wall.symlink_to(str(files[0].relative_to(ROOT)))
write('README.md','''# Dreamcore

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
''')
# Keep spotify-qt on the same shared palette without changing account settings.
subprocess.run(['python3', str(ROOT / '.config/spotify-qt/build-style.py')], check=True)
print(f'Built {ROOT}; 14 source colors; minimum checked text contrast {min(r["ratio"] for r in report):.2f}:1')
