# MyClipboard 📋

A secure, lightweight, cross-platform clipboard history manager built with Python and Tkinter.

## Features
- **Secure by Design**: Clipboard history is stored strictly in-memory and is never written to disk, ensuring sensitive data (like passwords or API keys) doesn't leak.
- **Unobtrusive UI**: Features a semi-transparent, always-on-top window that updates quietly without stealing your active window focus.
- **Easy Retrieval**: Double-click any item in your history list to instantly copy it back to your active clipboard.
- **Cross-Platform**: Built purely on Python's `tkinter` library, allowing it to work natively on Linux (X11/Wayland), macOS, and Windows.

## Installation & Requirements

Ensure you have Python 3 installed. You will also need the following dependencies:

1. **Pyperclip**: Used for interacting with the native OS clipboard.
   ```bash
   pip install pyperclip
   ```

2. **Tkinter** (Linux only): If you are on Ubuntu/Debian, Tkinter is not always installed by default.
   ```bash
   sudo apt-get install python3-tk
   ```

## Usage

Simply run the application using Python:
```bash
python3 app-home.py
```

## Linux Desktop Integration (Optional)

You can comfortably install MyClipboard as a native desktop application on Linux environments by creating a `.desktop` shortcut.

1. Create a file at `~/.local/share/applications/MyClipboard.desktop`.
2. Add the following configuration (be sure to replace `/absolute/path/to/` with the actual path to your cloned repository):

```ini
[Desktop Entry]
Version=1.0
Type=Application
Name=MyClipboard
Comment=Secure Clipboard History Manager
Exec=python3 /absolute/path/to/MyClipboard/app-home.py
Icon=edit-paste
Terminal=false
Categories=Utility;
```

3. Update your desktop database:
```bash
update-desktop-database ~/.local/share/applications
```

You can now launch "MyClipboard" directly from your system Application Menu!
