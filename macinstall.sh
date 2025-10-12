#!/usr/bin/env bash
set -euo pipefail

SRC="fch.py"

if [ ! -f "$SRC" ]; then
  echo "error: $SRC not found" >&2
  exit 1
fi

PY="$(command -v python3 || true)"
if [ -z "$PY" ]; then
  echo "error: python3 not found" >&2
  exit 1
fi

VENV_DIR="/usr/local/fch"
PLIST="$HOME/Library/LaunchAgents/com.local.fch.plist"
OUT_LOG="/var/log/fch.out.log"
ERR_LOG="/var/log/fch.err.log"

if [ ! -d "$VENV_DIR" ]; then
  sudo mkdir -p "$VENV_DIR"
  sudo chown "$(id -un)" "$VENV_DIR"
fi

"$PY" -m venv "$VENV_DIR"
"$VENV_DIR/bin/python" -m pip install --upgrade pip setuptools wheel

"$VENV_DIR/bin/python" -m pip install PyYAML pystray pyperclip Pillow pyobjc

install -m 755 "$SRC" "$VENV_DIR/fch.py"

echo "Installed: venv -> $VENV_DIR, script -> $VENV_DIR/fch.py"

sudo touch "$OUT_LOG" "$ERR_LOG"
sudo chown "$(id -un)" "$OUT_LOG" "$ERR_LOG"
sudo chmod 644 "$OUT_LOG" "$ERR_LOG"

mkdir -p "$HOME/Library/LaunchAgents"

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
         "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
 <dict>
   <key>Label</key>
   <string>com.local.fch</string>

   <key>ProgramArguments</key>
   <array>
     <string>$VENV_DIR/bin/python</string>
     <string>$VENV_DIR/fch.py</string>
   </array>

   <key>RunAtLoad</key>
   <true/>

   <key>KeepAlive</key>
   <true/>

   <key>StandardOutPath</key>
   <string>$OUT_LOG</string>

   <key>StandardErrorPath</key>
   <string>$ERR_LOG</string>
 </dict>
</plist>
EOF

chmod 644 "$PLIST"

launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST"

echo "Autostart enabled via launchd: $PLIST"
echo "Logs: $OUT_LOG, $ERR_LOG"
echo ""
echo "provide an icon at ~/.fch.png"

# ^ to ssie taką masywną pałe że nawet nie wiesz ale sie nie znam tak na bashu :(