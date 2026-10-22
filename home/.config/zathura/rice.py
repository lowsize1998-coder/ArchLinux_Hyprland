#!/usr/bin/env python3
"""Connect native Zathura settings to Symphony and its D-Bus interface."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
STATE = Path.home()/".local/state/zathura-rice/profiles"
SOURCE = Path.home()/".config/symphony/current/.config/gtk-3.0/colors.css"
MODES = ("rice", "paper", "warm", "original")
BUS = re.compile(r"org\.pwmt\.zathura\.PID[-_]?\d+")


def atomic(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text() == content:
        return
    fd, name = tempfile.mkstemp(prefix=".rice-", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as handle:
            handle.write(content)
        os.chmod(name, 0o644)
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def settings():
    data = json.loads((ROOT/"settings.json").read_text())
    if data["profile"] not in MODES:
        raise ValueError("Unknown reading profile")
    for key, low, high in [("pagePadding",0,100),("scrollStep",1,500),("zoomStep",1,100),
                           ("breakMinutes",0,180),("breakSeconds",1,300),
                           ("epubFontSize",8,40),("epubLineHeight",1,3),("epubParagraphSpacing",0,3)]:
        if not isinstance(data[key], (float,int)) or not low <= data[key] <= high:
            raise ValueError(f"Invalid setting: {key}")
    return data


def palette(source):
    definitions = dict(re.findall(r"@define-color\s+([\w-]+)\s+([^;]+);",source.read_text()))
    def resolve(key, seen=()):
        value = definitions.get(key, "").strip()
        if key in seen:
            raise ValueError(f"Cyclic color: {key}")
        if re.fullmatch(r"#[0-9a-fA-F]{6}", value):
            return value.lower()
        if value.startswith("@"):
            return resolve(value[1:], (*seen,key))
        raise ValueError(f"Unsupported palette color: {key}")
    return {name:resolve(key) for name,key in {
        "bg":"background","fg":"foreground","panel":"sidebar_bg_color",
        "accent":"cyan","muted":"white","error":"destructive_bg_color",
        "warning":"warning_bg_color"}.items()}


def build(source=SOURCE):
    p = palette(source)
    s = settings()
    independent = source.parent.parent / "zathura"
    def color(value):
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
            raise ValueError(f"Invalid profile color: {value}")
        return value
    def line(key, value):
        if isinstance(value,bool): value = str(value).lower()
        elif isinstance(value,str): value = json.dumps(value,ensure_ascii=False)
        return f"set {key} {value}\n"
    pairs = {
        "default-bg":p["bg"],"default-fg":p["fg"],
        "statusbar-bg":p["panel"],"statusbar-fg":p["fg"],
        "inputbar-bg":p["panel"],"inputbar-fg":p["fg"],
        "completion-bg":p["panel"],"completion-fg":p["fg"],
        "completion-group-bg":p["bg"],"completion-group-fg":p["muted"],
        "completion-highlight-bg":p["accent"],"completion-highlight-fg":p["bg"],
        "notification-bg":p["panel"],"notification-fg":p["fg"],
        "notification-error-bg":p["error"],"notification-error-fg":p["fg"],
        "notification-warning-bg":p["warning"],"notification-warning-fg":p["bg"],
        "index-bg":p["panel"],"index-fg":p["fg"],
        "index-active-bg":p["accent"],"index-active-fg":p["bg"],
        "render-loading-bg":p["bg"],"render-loading-fg":p["fg"],
        "highlight-color":p["accent"]+"60","highlight-active-color":p["accent"]+"a0",
        "highlight-fg":p["bg"],
    }
    appearance = "# Generated from Symphony: " + source.resolve().parents[2].name + "\n"
    if not (independent/"appearance").is_file():
        atomic(ROOT/"appearance", appearance + "".join(line(k,v) for k,v in pairs.items()))
    preferences = {
        "font":s["font"],"guioptions":"s","adjust-open":"width",
        "pages-per-row":1,"page-v-padding":s["pagePadding"],"page-h-padding":s["pagePadding"],
        "scroll-step":s["scrollStep"],"scroll-full-overlap":0.15,
        "zoom-step":s["zoomStep"],"selection-clipboard":"clipboard",
        "window-title-basename":True,"window-title-page":True,
        "statusbar-basename":True,"incremental-search":True,
        "statusbar-h-padding":12,"statusbar-v-padding":5,
    }
    atomic(ROOT/"preferences", "# Generated from settings.json\n" + "".join(line(k,v) for k,v in preferences.items()))
    epub_css = (
        '/* Generated from settings.json; add your own styles in epub-custom.css. */\n'
        f'body {{ font-family: {s["epubFont"]}; font-size: {s["epubFontSize"]}pt !important; '
        f'line-height: {s["epubLineHeight"]} !important; }}\n'
        f'p, li, blockquote {{ line-height: {s["epubLineHeight"]} !important; }}\n'
        f'p {{ margin-bottom: {s["epubParagraphSpacing"]}em !important; }}\n'
        'pre, code { font-family: monospace; }\n'
    )
    epub_css += (ROOT/"epub-custom.css").read_text()
    atomic(ROOT/"epub.css",epub_css)
    profiles = {"rice":{"background":p["bg"],"foreground":p["fg"]}, **s["profiles"]}
    for mode in MODES:
        if mode == "original":
            content = line("recolor",False)
        else:
            values = profiles[mode]
            content = line("recolor-darkcolor",color(values["foreground"]))
            content += line("recolor-lightcolor",color(values["background"]))
            content += line("recolor-keephue",True) + line("recolor-reverse-video",True) + line("recolor",True)
        if not (independent/"profiles"/mode).is_file():
            atomic(ROOT/"profiles"/mode,content)
        if mode == s["profile"]:
            if not (independent/"profiles/default").is_file():
                atomic(ROOT/"profiles/default",content)


def dbus(bus, method, *arguments):
    if not BUS.fullmatch(bus):
        raise ValueError(f"Invalid Zathura bus name: {bus}")
    result = subprocess.run(["gdbus","call","--session","--dest",bus,
        "--object-path","/org/pwmt/zathura","--method","org.pwmt.zathura."+method,*arguments],
        capture_output=True,text=True,timeout=5)
    if result.returncode or "true" not in result.stdout:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())


def buses():
    result = subprocess.run(["gdbus","call","--session","--dest","org.freedesktop.DBus",
        "--object-path","/org/freedesktop/DBus","--method","org.freedesktop.DBus.ListNames"],
        capture_output=True,text=True,timeout=5,check=True)
    return list(dict.fromkeys(BUS.findall(result.stdout)))


def mode_for(bus):
    file = STATE/bus
    mode = file.read_text().strip() if file.exists() else settings()["profile"]
    return mode if mode in MODES else "rice"


def apply(mode, bus):
    for command in (ROOT/"profiles"/mode).read_text().splitlines():
        if command.startswith("set "): dbus(bus,"ExecuteCommand",command)
    atomic(STATE/bus,mode+"\n")


def refresh(target=None, full=False):
    for bus in [target] if target else buses():
        try:
            mode = mode_for(bus)
            if full:
                dbus(bus,"SourceConfigFromDirectory",str(ROOT))
            else:
                for command in (ROOT/"appearance").read_text().splitlines():
                    if command.startswith("set "): dbus(bus,"ExecuteCommand",command)
            apply(mode,bus)
        except (RuntimeError,subprocess.SubprocessError) as error:
            print(f"Zathura reload: {error}",file=sys.stderr)


def main():
    command = sys.argv[1] if len(sys.argv)>1 else "launch"
    if command == "build":
        parser = argparse.ArgumentParser()
        parser.add_argument("--source",type=Path,default=SOURCE)
        parser.add_argument("--live",action="store_true")
        args = parser.parse_args(sys.argv[2:])
        build(args.source)
        if args.live: refresh()
    elif command == "reload":
        build()
        refresh(sys.argv[2] if len(sys.argv)>2 else None, full=True)
    elif command == "profile":
        mode = sys.argv[2]
        if mode not in MODES: raise ValueError("Choose rice, paper, warm or original")
        build()
        for bus in [sys.argv[3]] if len(sys.argv)>3 else buses(): apply(mode,bus)
    elif command == "breaks":
        action = sys.argv[2]
        operation = {"on":"start","off":"stop","status":"status"}[action]
        subprocess.run(["systemctl","--user",operation,"zathura-breaks.service"],check=True)
    else:
        build()
        subprocess.run(["systemctl","--user","start","zathura-breaks.service"],check=False,stdout=subprocess.DEVNULL)
        os.environ["GDK_BACKEND"] = "wayland"
        files = sys.argv[2:] if command == "launch" else sys.argv[1:]
        if not files:
            try:
                clients = json.loads(subprocess.check_output(["hyprctl","-j","clients"],text=True,timeout=3))
                readers = [c for c in clients if c.get("class") in {"org.pwmt.zathura","Zathura","zathura"} and c.get("mapped")]
                if readers:
                    window = min(readers,key=lambda c:c.get("focusHistoryID",999))
                    action = "hl.dsp.focus({window = " + json.dumps("address:"+window["address"]) + "})"
                    subprocess.run(["hyprctl","dispatch",action],check=True,timeout=3)
                    return
            except (OSError,ValueError,subprocess.SubprocessError): pass
            selection = subprocess.run(["zenity","--file-selection","--title=Открыть книгу в Zathura",
                "--file-filter=Документы | *.pdf *.epub *.djvu *.djv *.cbz *.cbr *.cb7 *.cbt *.ps *.eps *.xps *.oxps",
                "--file-filter=Все файлы | *"],capture_output=True,text=True)
            if selection.returncode: return
            files = [selection.stdout.rstrip("\n")]
        os.execvp("zathura",["zathura",*files])


if __name__ == "__main__":
    try: main()
    except (OSError,ValueError,KeyError,RuntimeError,subprocess.SubprocessError) as error:
        print(f"Zathura rice: {error}",file=sys.stderr)
        sys.exit(1)
