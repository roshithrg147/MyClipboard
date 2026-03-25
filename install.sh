#!/usr/bin/env bash

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#                                Author: RR                                     #
#                                Software Architect                             #
#                                Pilatewaveai                                   #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

set -e

echo "================================================"
echo "    Installing MyClipboard Enterprise..."
echo "================================================"

INSTALL_DIR="$HOME/.local/share/MyClipboard"
BIN_DIR="$HOME/.local/bin"
OS=$(uname -s)

# 1. Prepare directories
mkdir -p "$INSTALL_DIR"
mkdir -p "$BIN_DIR"

# 2. Copy application files (if running locally) or clone (if curl'd)
if [ -f "app/main.py" ]; then
    echo "[*] Copying application files..."
    cp -r app pyproject.toml README.md myclipboard.service "$INSTALL_DIR/"
else
    echo "[*] Cloning repository..."
    git clone https://github.com/roshithrg147/MyClipboard.git "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"

# 3. Create Virtual Environment
echo "[*] Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install .

# 4. Integrate with System (OS-specific)
if [ "$OS" == "Darwin" ]; then
    echo "[*] Detected macOS (Darwin). Setting up LaunchAgent..."
    PLIST_DIR="$HOME/Library/LaunchAgents"
    mkdir -p "$PLIST_DIR"
    PLIST_FILE="$PLIST_DIR/com.user.myclipboard.plist"
    
    cat <<EOF > "$PLIST_FILE"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.myclipboard</string>
    <key>ProgramArguments</key>
    <array>
        <string>$INSTALL_DIR/venv/bin/myclipboard</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$INSTALL_DIR</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
EOF
    # Load the agent
    launchctl unload "$PLIST_FILE" 2>/dev/null || true
    launchctl load "$PLIST_FILE"
    echo "[*] Registered MyClipboard as a LaunchAgent."

elif [ "$OS" == "Linux" ]; then
    echo "[*] Detected Linux. Setting up Desktop Entry and Systemd..."
    # Desktop Entry
    DESKTOP_FILE="$HOME/.local/share/applications/MyClipboard.desktop"
    mkdir -p "$HOME/.local/share/applications"
    cat <<EOF > "$DESKTOP_FILE"
[Desktop Entry]
Version=1.0
Type=Application
Name=MyClipboard Enterprise
Comment=Secure Clipboard History Manager
Exec=$INSTALL_DIR/venv/bin/myclipboard
WorkingDirectory=$INSTALL_DIR
Icon=edit-paste
Terminal=false
Categories=Utility;Security;
EOF
    update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true

    # Systemd Service
    SYSTEMD_DIR="$HOME/.config/systemd/user"
    mkdir -p "$SYSTEMD_DIR"
    cat <<EOF > "$SYSTEMD_DIR/myclipboard.service"
[Unit]
Description=MyClipboard Enterprise Manager
After=graphical-session.target
PartOf=graphical-session.target

[Service]
ExecStart=$INSTALL_DIR/venv/bin/myclipboard
WorkingDirectory=$INSTALL_DIR
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=graphical-session.target
EOF
    systemctl --user daemon-reload
    systemctl --user enable --now myclipboard.service
    echo "[*] Registered MyClipboard as a background service via systemd."
fi

# 5. Make CLI accessible
ln -sf "$INSTALL_DIR/venv/bin/myclipboard" "$BIN_DIR/myclipboard"

# Also link the direct 'mcb' command if not already available through entrypoints
# Actually, pyproject.toml already handles 'myclipboard' entrypoint.
# Let's add 'mcb' specifically as requested for developer ergonomics.
cat <<EOF > "$BIN_DIR/mcb"
#!/bin/bash
"$INSTALL_DIR/venv/bin/python3" "$INSTALL_DIR/app/main.py" --mcb "\$@"
EOF
# Wait, let's keep it simple. If mcb.py is separate, use it.
cp mcb.py "$INSTALL_DIR/"
ln -sf "$INSTALL_DIR/venv/bin/python3 $INSTALL_DIR/mcb.py" "$BIN_DIR/mcb" 2>/dev/null || true
# Fixing the symlink for mcb
cat <<EOF > "$BIN_DIR/mcb"
#!/bin/bash
$INSTALL_DIR/venv/bin/python3 $INSTALL_DIR/mcb.py "\$@"
EOF
chmod +x "$BIN_DIR/mcb"

echo "================================================"
echo "    Installation Complete!"
echo "    - Background service is running ($OS)."
echo "    - Commands available: 'myclipboard', 'mcb'."
echo "    - You can type 'myclipboard' in your terminal"
echo "      to summon the UI at any time."
echo "================================================"
