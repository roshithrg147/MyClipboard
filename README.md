<!--
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#                                Author: RR                                     #
#                                Software Architect                             #
#                                Pilatewaveai                                   #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
-->
# MyClipboard Enterprise 📋

An enterprise-grade, secure, multi-threaded, and cross-platform clipboard manager.

## 🚀 Key Features
- **Strict In-Memory Security**: Encrypted RAM history using `cryptography`. History is never written to disk.
- **Terminal Awareness**: Automatically pauses recording when sensitive applications (Terminal, iTerm, SSH, Vault) are active.
- **DLP Masking**: Masking for AWS keys, Credit Cards, SSH keys, etc., within the history UI.
- **Multi-Paste Buffer**: Staged sequential paste via `Ctrl+Alt+V`.
- **Global Hotkeys**: Summon the UI with `Ctrl+Shift+V` from anywhere.
- **CLI Integration**: Use `mcb` to pipe terminal output directly into your clipboard history.
- **Templates**: Instant access to your most-used text snippets.

## 🛠️ Installation & Requirements

### One-Line Install (Recommended)
Installs the background daemon, desktop shortcuts, and global commands:
```bash
bash install.sh
```

### System Dependencies
- **Linux**: `sudo apt install python3-tk xclip`
- **macOS**: `brew install python-tk` (Requires Accessibility permissions for hotkeys)

### Python Setup (Manual)
```bash
pip install .
```

## 💻 Usage
- **Show History**: `Ctrl+Shift+V` or type `myclipboard`.
- **Search**: Start typing once the UI appears.
- **Pipe Output**: `echo "test" | mcb`
- **Paste Next in Queue**: `Ctrl+Alt+V`

## ⚙️ Enterprise Integration
- **Linux**: Managed via `systemd` (`--user` level).
- **macOS**: Managed via `launchd` (`LaunchAgents`).
- **Persistence**: Encrypted keys are ephemeral. On restart, history is cleared.

---
© 2026 RR, Pilatewaveai. All Rights Reserved.
