#!/bin/bash

# MyClipboard Enterprise v2.0 Installer
# Author: RR

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/venv"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"

echo "📋 Initializing MyClipboard Enterprise v2.0 Installer..."

# 1. Setup Virtual Environment
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

echo "Installing dependencies..."
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -r "$PROJECT_DIR/requirements.txt"

# 2. Create Global Binary
mkdir -p "$BIN_DIR"
cat <<EOF > "$BIN_DIR/myclipboard"
#!/bin/bash
export PYTHONPATH="$PROJECT_DIR"
"$VENV_DIR/bin/python3" "$PROJECT_DIR/app/main.py" "\$@"
EOF
chmod +x "$BIN_DIR/myclipboard"

# 3. Create mcb CLI Binary
cat <<EOF > "$BIN_DIR/mcb"
#!/bin/bash
export PYTHONPATH="$PROJECT_DIR"
"$VENV_DIR/bin/python3" "$PROJECT_DIR/mcb.py" "\$@"
EOF
chmod +x "$BIN_DIR/mcb"

# 4. Create Desktop Entry (to show in Apps menu)
mkdir -p "$DESKTOP_DIR"
cat <<EOF > "$DESKTOP_DIR/myclipboard.desktop"
[Desktop Entry]
Name=MyClipboard Enterprise
Comment=Secure, AI-powered Clipboard Manager
Exec=$BIN_DIR/myclipboard
Icon=terminal
Terminal=false
Type=Application
Categories=Utility;
Keywords=clipboard;copy;paste;ghost;
EOF
chmod +x "$DESKTOP_DIR/myclipboard.desktop"

# 5. Refresh Desktop Database
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$DESKTOP_DIR"
fi

echo "✅ Installation complete!"
echo "🚀 'MyClipboard Enterprise' is now available in your Applications menu."
echo "⌨️ Global Hotkeys (Currently: ctl+shift+q) will be active while running."
echo "Note: Ensure $BIN_DIR is in your PATH."
