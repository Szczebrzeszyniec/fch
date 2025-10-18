#!/usr/bin/python3
import time
import yaml
import os
import pystray
from PIL import Image
import pyperclip
from threading import Thread
import subprocess
from AppKit import NSApplication, NSApplicationActivationPolicyProhibited

app = NSApplication.sharedApplication()
app.setActivationPolicy_(NSApplicationActivationPolicyProhibited)

CONF = os.path.expanduser("~/.ftools/fch/config.yaml")
HIST = os.path.expanduser("~/.ftools/fch/history.yaml")
ICON = os.path.expanduser("~/.ftools/fch/icon.png")
HISTORY = []
HISTLIM = 3
HISTMAX = 8
HISTSTORE = 0
CAP = True

def check():
    os.makedirs(os.path.dirname(CONF), exist_ok=True)
    if not os.path.exists(CONF):
        with open(CONF, "w", encoding="utf-8") as f:
            yaml.safe_dump({"limit": 3, "max": 8, "store": 9999}, f)
    if not os.path.exists(HIST):
        with open(HIST, "w", encoding="utf-8") as f:
            yaml.safe_dump("", f)


def read(key):
    try:
        with open(CONF, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except Exception:
        data = {}
    return data.get(key)

def readAll():
    try:
        with open(CONF, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except Exception:
        data = {}
    return list(data.keys())

def write(name, conf):
    try:
        with open(CONF, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except Exception:
        data = {}
    data[name] = conf
    with open(CONF, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False)

def getConfig():
    global HISTLIM, HISTMAX, HISTSTORE
    limit = read("limit")
    if isinstance(limit, int) and limit >= 0:
        HISTLIM = limit
    extra_max = read("max")
    if isinstance(extra_max, int) and extra_max >= 0:
        HISTMAX = HISTLIM + extra_max
    else:
        HISTMAX = HISTLIM + 5
    store = read("store")
    if isinstance(store, int) and store >= 0:
        HISTSTORE = store
    else:
        HISTSTORE = 0

def loadHistory():
    global HISTORY
    try:
        with open(HIST, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            HISTORY = data if isinstance(data, list) else []
    except Exception:
        HISTORY = []

def saveHistory():
    global HISTORY, HISTSTORE
    if isinstance(HISTSTORE, int) and HISTSTORE > 0 and len(HISTORY) > HISTSTORE:
        HISTORY = HISTORY[-HISTSTORE:]
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
    try:
        pyperclip.copy(text)
    except Exception:
        pass

def quit(icon, item=None):
    icon.stop()

def toglCap(icon=None, item=None):
    global CAP
    CAP = not CAP
    rebuildMenu(icon)

def rebuildMenu(icon):
    items = []
    hist = list(reversed(HISTORY))

    if len(hist) > HISTLIM:
        visible = hist[:HISTLIM]
        remaining = hist[HISTLIM:HISTMAX]

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
        items.append(pystray.Menu.SEPARATOR)

        appmenu = []
        if CAP:
            appmenu.append(pystray.MenuItem("Stop capture", lambda: toglCap(icon)))
        else:
            appmenu.append(pystray.MenuItem("Start capture", lambda: toglCap(icon)))

        appmenu.append(pystray.MenuItem("Configure", confEdit))
        appmenu.append(pystray.MenuItem("Exit Process", quit))
        items.append(pystray.MenuItem("Application", pystray.Menu(*appmenu)))

    else:
        for entry in hist:
            lbl = label(entry, 40)

            def make_cb(t):
                def cb(*_args, **_kwargs):
                    on_select(icon, t)
                return cb

            items.append(pystray.MenuItem(lbl, make_cb(entry)))

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
    if not CAP:
        return
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

def confEdit(icon=None, item=None):
    subprocess.run(["open", "-e", CONF])

def confWatch(icon, poll_interval=1.0):
    last_conf_mtime = None
    last_hist_mtime = None
    while True:
        try:
            conf_mtime = os.path.getmtime(CONF) if os.path.exists(CONF) else None
        except Exception:
            conf_mtime = None
        try:
            hist_mtime = os.path.getmtime(HIST) if os.path.exists(HIST) else None
        except Exception:
            hist_mtime = None
        if conf_mtime != last_conf_mtime:
            last_conf_mtime = conf_mtime
            try:
                getConfig()
            except Exception:
                pass
            try:
                rebuildMenu(icon)
            except Exception:
                pass
        if hist_mtime != last_hist_mtime:
            last_hist_mtime = hist_mtime
            try:
                loadHistory()
            except Exception:
                pass
            try:
                rebuildMenu(icon)
            except Exception:
                pass
        time.sleep(poll_interval)

def setup(icon):
    loadHistory()
    getConfig()
    rebuildMenu(icon)
    watcher = Thread(target=clipbWatch, args=(icon,), daemon=True)
    watcher.start()
    cfg_w = Thread(target=confWatch, args=(icon,), daemon=True)
    cfg_w.start()

def main():
    check()
    image = makeIco()
    icon = pystray.Icon("fch", image, "fch")
    icon.visible = True
    icon.run(setup)

if __name__ == "__main__":
    main()
