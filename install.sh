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

# 4. Create Desktop Entry
echo "[*] Integrating with Desktop Environment..."
DESKTOP_FILE="$HOME/.local/share/applications/MyClipboard.desktop"
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

# 5. Install Systemd Service
echo "[*] Registering Background Service..."
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

# 6. Make CLI accessible
ln -sf "$INSTALL_DIR/venv/bin/myclipboard" "$BIN_DIR/myclipboard"

echo "================================================"
echo "    Installation Complete!"
echo "    - Background service is running."
echo "    - You can type 'myclipboard' in your terminal"
echo "      to summon the UI at any time."
echo "================================================"
