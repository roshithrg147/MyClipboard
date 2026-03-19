import os
import sys
import queue
import logging
import signal
import tkinter as tk
from typing import List

# Setup standard enterprise logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Verify system dependencies
def verify_environment():
    if sys.platform.startswith("linux"):
        from shutil import which
        # Checking for standard X11 / Wayland tools that pyperclip wraps silently
        if not (which("xclip") or which("xsel") or which("wl-clipboard")):
            logger.error("System dependency missing: xclip, xsel, or wl-clipboard is required on Linux.")
            sys.exit(1)

verify_environment()

from app.service import ClipboardService

class ClipboardConsumerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.update_queue = queue.Queue()
        self.service = ClipboardService(update_queue=self.update_queue)
        
        self.history: List[str] = []
        self._setup_ui()
        self._setup_signals()
        
        self.service.start()
        self._process_queue()

    def _setup_ui(self):
        self.root.title("MyClipboard Enterprise")
        self.root.geometry("400x500")
        self.root.attributes('-topmost', True)
        self.root.attributes('-alpha', 0.8)
        
        self.listbox = tk.Listbox(self.root, font=("Helvetica", 11), selectmode=tk.SINGLE)
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.listbox.bind("<Double-Button-1>", self.on_double_click)
        
        # Graceful exit on window close
        self.root.protocol("WM_DELETE_WINDOW", self.shutdown)

    def _setup_signals(self):
        # Register OS signal handlers for completely secure shutdown
        def _signal_handler(sig, frame):
            logger.info(f"Received signal {sig}. Initiating secure shutdown.")
            self.shutdown()
            
        signal.signal(signal.SIGINT, _signal_handler)
        signal.signal(signal.SIGTERM, _signal_handler)

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
        self.root.destroy()
        sys.exit(0)

def main():
    root = tk.Tk()
    app = ClipboardConsumerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
