<!--
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#                                Author: RR                                     #
#                                Software Architect                             #
#                                Pilatewaveai                                   #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
-->
# MyClipboard Enterprise 📋

An enterprise-grade, secure, lightweight, and cross-platform clipboard history manager. Engineered for productivity and designed with strict security principles to ensure your sensitive data remains protected.

## 🚀 Key Features

- **Strict In-Memory Security**: Clipboard history is never written to disk. When memory is cleared, references are explicitly overwritten in RAM before garbage collection, mitigating memory-scraping attacks.
- **System Tray Integration**: Runs silently in the background. The UI remains hidden until summoned, preserving screen real estate.
- **Single-Instance Enforcement**: Utilizes IPC (Unix Sockets) to guarantee only one instance runs. Launching the application again seamlessly summons the existing background instance.
- **Unobtrusive & Responsive UI**: Features a semi-transparent, always-on-top overlay that updates quietly without stealing active window focus.
- **Instant Retrieval**: Double-click any item in your history queue to instantly restore it to your active clipboard.
- **Daemon-Ready**: Includes native `systemd` integration for automated startup with your graphical session.

## 🛠️ Installation & Requirements

Ensure you have Python 3.8+ installed. 

### One-Line Install (Recommended)
You can seamlessly install MyClipboard as a system application (including background daemon, desktop icon, and `myclipboard` terminal command) by running:
```bash
bash install.sh
```

### Manual Installation
If you prefer to install manually:

#### 1. System Dependencies (Linux)
MyClipboard relies on native OS clipboards and Tkinter. On Debian/Ubuntu systems:
```bash
sudo apt-get update
sudo apt-get install python3-tk xclip # or xsel / wl-clipboard for Wayland
```

### 2. Python Dependencies
Install the required packages using `pip`:
```bash
pip install -r pyproject.toml
# Or install manually:
pip install pyperclip pystray Pillow
```

## 💻 Usage

Run the application module directly:
```bash
python3 -m app.main
```
The application will launch in the background. Look for the MyClipboard icon in your system tray to access your history or quit the application. Running the command a second time will bring the hidden window to the front.

## ⚙️ Enterprise Integration

### Background Service (Systemd)

To run MyClipboard seamlessly as a background daemon on Linux:

1. Copy the provided service file to your user systemd directory:
   ```bash
   mkdir -p ~/.config/systemd/user/
   cp myclipboard.service ~/.config/systemd/user/
   ```
2. Update the `WorkingDirectory` and `ExecStart` paths in the copied `myclipboard.service` file to match your deployment path.
3. Reload systemd and enable the service:
   ```bash
   systemctl --user daemon-reload
   systemctl --user enable --now myclipboard.service
   ```

### Desktop Integration

To add MyClipboard to your application launcher:

1. Create a file at `~/.local/share/applications/MyClipboard.desktop`:
   ```ini
   [Desktop Entry]
   Version=1.0
   Type=Application
   Name=MyClipboard Enterprise
   Comment=Secure Clipboard History Manager
   Exec=python3 -m app.main
   WorkingDirectory=/absolute/path/to/MyClipboard
   Icon=edit-paste
   Terminal=false
   Categories=Utility;Security;
   ```
2. Update your desktop database:
   ```bash
   update-desktop-database ~/.local/share/applications
   ```
