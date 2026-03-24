# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#                                Author: RR                                     #
#                                Software Architect                             #
#                                Pilatewaveai                                   #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

import os
import sys
import queue
import logging
import signal
import socket
import threading
import tkinter as tk
import tkinter.ttk as ttk
from typing import List, Tuple
import pystray
from PIL import Image

try:
    from pynput import keyboard
except ImportError:
    logging.warning("pynput package is missing. Global hotkeys will be disabled. Install with: pip install pynput")
    keyboard = None

# Setup standard enterprise logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

SOCKET_PATH = "/tmp/myclipboard.sock"

# Verify system dependencies
def verify_environment():
    if sys.platform.startswith("linux"):
        from shutil import which
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
        self.filtered_history: List[Tuple[int, str]] = []
        
        # Load templates from service
        self.templates = self.service.get_templates()
        self.filtered_templates: List[Tuple[int, str]] = []
        
        self.socket_thread = threading.Thread(target=self._ipc_listener, daemon=True)
        self.socket_thread.start()
        
        self._setup_ui()
        self._setup_signals()
        self._setup_tray()
        self._setup_hotkeys()
        
        self.service.start()
        self._process_queue()

    def _setup_ui(self):
        self.root.title("MyClipboard Enterprise")
        self.root.geometry("450x600")
        
        # Search Bar Frame
        search_frame = tk.Frame(self.root)
        search_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        tk.Label(search_frame, text="Search:", font=("Helvetica", 10, "bold")).pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self._on_search_change)
        
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var, font=("Helvetica", 11))
        self.search_entry.pack(fill=tk.X, expand=True, padx=(5, 0))
        self.root.bind("<Map>", lambda e: self.search_entry.focus_set())
        
        # Notebook for Tabs
        style = ttk.Style()
        style.theme_use('default')
        style.configure('TNotebook.Tab', font=('Helvetica', 10, 'bold'), padding=[10, 5])
        
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_change)
        
        # History Tab
        self.history_frame = tk.Frame(self.notebook)
        self.notebook.add(self.history_frame, text="History")
        self.listbox = tk.Listbox(self.history_frame, font=("Helvetica", 11), selectmode=tk.EXTENDED)
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.listbox.bind("<Double-Button-1>", self.on_double_click)
        self.listbox.bind("<Return>", self.on_double_click)
        self.listbox.bind("<Button-3>", self.on_right_click)
        
        # Templates Tab
        self.templates_frame = tk.Frame(self.notebook)
        self.notebook.add(self.templates_frame, text="Templates")
        self.template_listbox = tk.Listbox(self.templates_frame, font=("Helvetica", 11), selectmode=tk.SINGLE)
        self.template_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.template_listbox.bind("<Double-Button-1>", self.on_template_double_click)
        self.template_listbox.bind("<Return>", self.on_template_double_click)
        
        # Smart Transform Context Menu
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Queue for Multi-Paste", command=self._trigger_multi_paste_queue)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Format JSON", command=lambda: self._trigger_transform("json"))
        self.context_menu.add_command(label="To camelCase", command=lambda: self._trigger_transform("camel"))
        self.context_menu.add_command(label="To snake_case", command=lambda: self._trigger_transform("snake"))
        self.context_menu.add_command(label="Encode Base64", command=lambda: self._trigger_transform("base64"))
        self.context_menu.add_command(label="Decode Base64", command=lambda: self._trigger_transform("base64_decode"))
        
        self.root.withdraw()
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)
        
        # Initial Render
        self._render_templates()

    def _setup_hotkeys(self):
        if keyboard is None:
            return
            
        def on_activate_h():
            self.root.after(0, self.show_window)
            
        def on_activate_multi_paste():
            self.service.pop_multi_paste()
            
        self.hotkey_listener = keyboard.GlobalHotKeys({
            '<ctrl>+<shift>+v': on_activate_h,
            '<ctrl>+<alt>+v': on_activate_multi_paste
        })
        self.hotkey_listener.start()

    def _on_search_change(self, *args):
        current_tab = self.notebook.index(self.notebook.select())
        if current_tab == 0:
            self._render_listbox()
        else:
            self._render_templates()

    def _on_tab_change(self, event):
        self._on_search_change()

    def hide_window(self):
        self.root.withdraw()

    def show_window(self):
        self.root.deiconify()
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.attributes('-alpha', 0.8)
        self.search_entry.focus_set()

    def _setup_signals(self):
        def _signal_handler(sig, frame):
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
            while True:
                conn, _ = server.accept()
                try:
                    chunks = []
                    while True:
                        chunk = conn.recv(4096)
                        if not chunk: break
                        chunks.append(chunk)
                    data = b"".join(chunks).decode('utf-8', errors='ignore')
                    
                    if data == "SHOW":
                        self.root.after(0, self.show_window)
                    elif data.startswith("ADD:"):
                        self.service.add_external_clip(data[4:])
                finally:
                    conn.close()
        except OSError: pass
        finally:
            if server: server.close()
            if os.path.exists(SOCKET_PATH):
                try: os.remove(SOCKET_PATH)
                except OSError: pass

    def _setup_tray(self):
        image = Image.new('RGB', (64, 64), color=(73, 109, 137))
        def on_quit(icon, item):
            icon.stop()
            self.root.after(0, self.shutdown)
        def on_show(icon, item):
            self.root.after(0, self.show_window)
        def on_toggle_pause(icon, item):
            self.service.toggle_pause()
            
        menu = pystray.Menu(
            pystray.MenuItem('Show MyClipboard', on_show, default=True),
            pystray.MenuItem('Pause/Resume Recording', on_toggle_pause),
            pystray.MenuItem('Quit', on_quit)
        )
        self.icon = pystray.Icon("MyClipboard", image, "MyClipboard", menu)
        self.tray_thread = threading.Thread(target=self.icon.run, daemon=True)
        self.tray_thread.start()

    def _process_queue(self):
        try:
            while True:
                msg = self.update_queue.get_nowait()
                if msg["type"] == "new_clip":
                    self.history = msg["data"]
                    self._render_listbox()
        except queue.Empty: pass
        self.root.after(100, self._process_queue)

    def _render_listbox(self):
        query = self.search_var.get().lower()
        self.listbox.delete(0, tk.END)
        self.filtered_history.clear()
        for original_idx, display_text in enumerate(self.history):
            if query in display_text.lower():
                self.filtered_history.append((original_idx, display_text))
                self.listbox.insert(tk.END, f"[{original_idx + 1}]  {display_text}")

    def _render_templates(self):
        query = self.search_var.get().lower()
        self.template_listbox.delete(0, tk.END)
        self.filtered_templates.clear()
        for original_idx, template_dict in enumerate(self.templates):
            title = template_dict.get("title", "Untitled")
            if query in title.lower():
                self.filtered_templates.append((original_idx, title))
                self.template_listbox.insert(tk.END, f"★  {title}")

    def on_double_click(self, event):
        selection = self.listbox.curselection()
        if selection:
            filtered_index = selection[0]
            if filtered_index < len(self.filtered_history):
                self.service.restore_from_index(self.filtered_history[filtered_index][0])
                self.hide_window()

    def on_template_double_click(self, event):
        selection = self.template_listbox.curselection()
        if selection:
            filtered_index = selection[0]
            if filtered_index < len(self.filtered_templates):
                self.service.restore_template(self.filtered_templates[filtered_index][0])
                self.hide_window()

    def on_right_click(self, event):
        clicked_index = self.listbox.nearest(event.y)
        if clicked_index not in self.listbox.curselection():
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(clicked_index)
            self.listbox.activate(clicked_index)
        self.context_menu.tk_popup(event.x_root, event.y_root)

    def _trigger_multi_paste_queue(self):
        selections = self.listbox.curselection()
        if selections:
            original_indices = [self.filtered_history[idx][0] for idx in selections if idx < len(self.filtered_history)]
            self.service.queue_multi_paste(original_indices)
            self.hide_window()

    def _trigger_transform(self, transform_type: str):
        selection = self.listbox.curselection()
        if selection:
            filtered_index = selection[0]
            if filtered_index < len(self.filtered_history):
                self.service.transform_item(self.filtered_history[filtered_index][0], transform_type)
                self.hide_window()

    def shutdown(self):
        self.service.stop()
        if hasattr(self, 'icon'): self.icon.stop()
        if hasattr(self, 'hotkey_listener'): self.hotkey_listener.stop()
        try:
            if os.path.exists(SOCKET_PATH): os.remove(SOCKET_PATH)
        except OSError: pass
        self.root.destroy()
        sys.exit(0)

def notify_existing_instance():
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        client.connect(SOCKET_PATH)
        client.sendall(b"SHOW")
        client.close()
        return True
    except Exception:
        try: os.remove(SOCKET_PATH)
        except OSError: pass
        return False

def main():
    if notify_existing_instance(): sys.exit(0)
    root = tk.Tk()
    app = ClipboardConsumerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
