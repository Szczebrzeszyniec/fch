#!/usr/bin/python3
# fch.py

import time
import yaml
import os
import pystray
from PIL import Image
import pyperclip
from threading import Thread
from AppKit import NSApplication, NSApplicationActivationPolicyProhibited

app = NSApplication.sharedApplication()
app.setActivationPolicy_(NSApplicationActivationPolicyProhibited)

CONF = os.path.expanduser("~/.fch.yaml")
HIST = os.path.expanduser("~/.fch-history.yaml")
ICON = os.path.expanduser("~/.fch.png")
HISTORY = []

def check():
    if not os.path.exists(CONF):
        open(CONF, "w").close()
    if not os.path.exists(HIST):
        with open(HIST, "w", encoding="utf-8") as f:
            yaml.safe_dump([], f)

def read(key):
    with open(CONF, "r") as f:
        data = yaml.safe_load(f) or {}
    return data.get(key)

def readAll():
    with open(CONF, "r") as f:
        data = yaml.safe_load(f) or {}
    return list(data.keys())


def write(name, conf):
    try:
        with open(CONF, "r") as f:
            data = yaml.safe_load(f) or {}
    except FileNotFoundError:
        data = {}
    data[name] = conf
    with open(CONF, "w") as f:
        yaml.safe_dump(data, f, sort_keys=False)

def loadHistory():
    global HISTORY
    try:
        with open(HIST, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            HISTORY = data if isinstance(data, list) else []
    except Exception:
        HISTORY = []

def saveHistory():
    with open(HIST, "w", encoding="utf-8") as f:
        yaml.safe_dump(HISTORY, f, sort_keys=False)

def makeIco():
    try:
        return Image.open(ICON)
    except Exception:
        return Image.new("RGBA", (64, 64), (0, 0, 0, 0))

def label(text, limit=40):
    first_line = text.splitlines()[0] if text else ""
    if len(first_line) > limit:
        return first_line[: limit - 1] + "…"
    return first_line or "(empty)"

def on_select(icon, text):
    pyperclip.copy(text)

def quit(icon, item=None):
    icon.stop()


def rebuildMenu(icon):
    items = []
    hist = list(reversed(HISTORY))
    if len(hist) > 10:
        visible = hist[:10]
        remaining = hist[10:]
        for entry in visible:
            lbl = label(entry, 40)
            def make_cb(t):
                def cb(*_args, **_kwargs):
                    on_select(icon, t)
                return cb
            items.append(pystray.MenuItem(lbl, make_cb(entry)))
        submenu = []
        for entry in remaining:
            lbl = label(entry, 40)
            def make_cb(t):
                def cb(*_args, **_kwargs):
                    on_select(icon, t)
                return cb
            submenu.append(pystray.MenuItem(lbl, make_cb(entry)))
        items.append(pystray.MenuItem("More...", pystray.Menu(*submenu)))
    else:
        for entry in hist:
            lbl = label(entry, 40)
            def make_cb(t):
                def cb(*_args, **_kwargs):
                    on_select(icon, t)
                return cb
            items.append(pystray.MenuItem(lbl, make_cb(entry)))
    items.append(pystray.MenuItem("Quit", quit))
    icon.menu = pystray.Menu(*items)
    try:
        icon.update_menu()
    except Exception:
        pass


def appendHist(text):
    text = text.rstrip("\n")
    if text == "":
        return
    if HISTORY and HISTORY[-1] == text:
        return
    HISTORY.append(text)
    saveHistory()

def clipbOnchange(new_text, icon):
    appendHist(new_text)
    rebuildMenu(icon)

def clipbWatch(icon, poll_interval=0.5):
    try:
        last_text = pyperclip.paste()
    except Exception:
        last_text = None
    while True:
        try:
            current = pyperclip.paste()
        except Exception:
            current = None
        if current is not None and current != last_text:
            last_text = current
            clipbOnchange(current, icon)
        time.sleep(poll_interval)

def setup(icon):
    loadHistory()
    rebuildMenu(icon)
    watcher = Thread(target=clipbWatch, args=(icon,), daemon=True)
    watcher.start()

def main():
    check()
    image = makeIco()
    icon = pystray.Icon("fch", image, "Clipboard history")
    icon.visible = True
    icon.run(setup)

if __name__ == "__main__":
    main()
