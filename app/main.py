import os
import sys
import queue
import logging
import signal
import socket
import threading
import tkinter as tk
from typing import List
import pystray
from PIL import Image

# Setup standard enterprise logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

SOCKET_PATH = "/tmp/myclipboard.sock"

# Verify system dependencies
def verify_environment():
    if sys.platform.startswith("linux"):
        from shutil import which
        # Checking for standard X11 / Wayland tools that pyperclip wraps silently
        if not (which("xclip") or which("xsel") or which("wl-clipboard")):
            logger.critical("System dependency missing: xclip, xsel, or wl-clipboard is required on Linux.")
            sys.exit(1)

verify_environment()

from app.service import ClipboardService

class ClipboardConsumerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.update_queue = queue.Queue()
        self.service = ClipboardService(update_queue=self.update_queue)
        
        self.history: List[str] = []
        
        # Start IPC Listener immediately
        self.socket_thread = threading.Thread(target=self._ipc_listener, daemon=True)
        self.socket_thread.start()
        
        self._setup_ui()
        self._setup_signals()
        self._setup_tray()
        
        self.service.start()
        self._process_queue()

    def _setup_ui(self):
        self.root.title("MyClipboard Enterprise")
        self.root.geometry("400x500")
        
        self.listbox = tk.Listbox(self.root, font=("Helvetica", 11), selectmode=tk.SINGLE)
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.listbox.bind("<Double-Button-1>", self.on_double_click)
        
        # Start hidden and hide on close
        self.root.withdraw()
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)

    def hide_window(self):
        logger.info("Hiding window...")
        self.root.withdraw()

    def show_window(self):
        logger.info("Showing window via IPC/Tray command...")
        self.root.deiconify()
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.attributes('-alpha', 0.8)

    def _setup_signals(self):
        # Register OS signal handlers for completely secure shutdown
        def _signal_handler(sig, frame):
            logger.info(f"Received signal {sig}. Initiating secure shutdown.")
            self.shutdown()
            
        signal.signal(signal.SIGINT, _signal_handler)
        signal.signal(signal.SIGTERM, _signal_handler)

    def _ipc_listener(self):
        server = None
        try:
            if os.path.exists(SOCKET_PATH):
                os.remove(SOCKET_PATH)
            
            server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            server.bind(SOCKET_PATH)
            server.listen(1)
            logger.info(f"Listening on Unix socket {SOCKET_PATH}")
            
            while True:
                conn, _ = server.accept()
                try:
                    data = conn.recv(1024).decode('utf-8')
                    if data == "SHOW":
                        # Push UI state change to the main Tkinter thread
                        self.root.after(0, self.show_window)
                except Exception as e:
                    logger.error(f"IPC connection error: {e}")
                finally:
                    conn.close()
        except OSError as e:
            logger.error(f"Failed to start IPC Server OSError: {e}")
        except Exception as e:
            logger.error(f"Failed to start IPC Server: {e}")
        finally:
            if server:
                server.close()
            if os.path.exists(SOCKET_PATH):
                try:
                    os.remove(SOCKET_PATH)
                except OSError:
                    pass

    def _setup_tray(self):
        # Create a blank 64x64 solid color image for the system tray icon
        image = Image.new('RGB', (64, 64), color=(73, 109, 137))
        
        def on_quit(icon, item):
            logger.info("Quit requested via System Tray.")
            icon.stop()
            self.root.after(0, self.shutdown)
            
        def on_show(icon, item):
            self.root.after(0, self.show_window)
            
        menu = pystray.Menu(
            pystray.MenuItem('Show MyClipboard', on_show, default=True),
            pystray.MenuItem('Quit', on_quit)
        )
        self.icon = pystray.Icon("MyClipboard", image, "MyClipboard", menu)
        
        self.tray_thread = threading.Thread(target=self.icon.run, daemon=True)
        self.tray_thread.start()

    def _process_queue(self):
        try:
            while True:
                # Process all pending updates in the queue
                msg = self.update_queue.get_nowait()
                if msg["type"] == "new_clip":
                    self.history = msg["data"]
                    self._render_listbox()
        except queue.Empty:
            pass
            
        # Schedule next queue polling non-blocking via Tkinter event loop
        self.root.after(100, self._process_queue)

    def _render_listbox(self):
        self.listbox.delete(0, tk.END)
        for idx, item in enumerate(self.history):
            # Safe truncation for rendering massive blocks
            display_text = item.replace('\n', ' ')
            if len(display_text) > 80:
                display_text = display_text[:77] + "..."
            self.listbox.insert(tk.END, f"[{idx + 1}]  {display_text}")

    def on_double_click(self, event):
        selection = self.listbox.curselection()
        if selection:
            index = selection[0]
            if index < len(self.history):
                selected_text = self.history[index]
                self.service.copy_to_clipboard(selected_text)

    def shutdown(self):
        logger.info("Executing graceful shutdown...")
        self.service.stop()
        if hasattr(self, 'icon'):
            self.icon.stop()
        
        # Explicit socket cleanup fallback
        try:
            if os.path.exists(SOCKET_PATH):
                os.remove(SOCKET_PATH)
        except OSError:
            pass
            
        self.root.destroy()
        sys.exit(0)

def notify_existing_instance():
    """Attempt to connect to the socket on startup."""
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        client.connect(SOCKET_PATH)
        client.sendall(b"SHOW")
        client.close()
        return True
    except ConnectionRefusedError:
        # Socket file exists but no process is listening. Clean it up so we can bind.
        try:
            os.remove(SOCKET_PATH)
        except OSError:
            pass
        return False
    except FileNotFoundError:
        return False
    except Exception as e:
        logger.error(f"Unexpected error checking socket: {e}")
        return False

def main():
    # Attempt instance lock / IPC ping
    if notify_existing_instance():
        logger.info("Application is already running. Sent 'SHOW' signal. Exiting.")
        sys.exit(0)
        
    root = tk.Tk()
    app = ClipboardConsumerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
