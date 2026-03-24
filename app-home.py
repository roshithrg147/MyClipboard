# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#                                Author: RR                                     #
#                                Software Architect                             #
#                                Pilatewaveai                                   #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


import pyperclip
import tkinter as tk
from collections import deque

class ClipboardManager:
    def __init__(self, root, history_limit=10):
        self.root = root
        self.history_limit = history_limit
        self.clipboard_history = deque(maxlen=history_limit)
        self.last_clip = None

        self.setup_ui()
        self.poll_clipboard()

    def setup_ui(self):
        self.root.title("Clipboard History")
        self.root.geometry("400x500")
        
        # Keep window always on top
        self.root.attributes('-topmost', True)
        
        # Set semi-transparency (only roughly works depending on WM, but cross-platform standard)
        self.root.attributes('-alpha', 0.8)
        
        # UI Elements
        self.listbox = tk.Listbox(self.root, font=("Helvetica", 11), selectmode=tk.SINGLE)
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Bind double click to copy back to clipboard
        self.listbox.bind("<Double-Button-1>", self.copy_to_clipboard)

    def poll_clipboard(self):
        try:
            current_clip = pyperclip.paste()
            if current_clip != self.last_clip and current_clip.strip() != "":
                self.clipboard_history.appendleft(current_clip)
                self.last_clip = current_clip
                self.update_ui()
        except pyperclip.PyperclipException:
            pass # Handle cases where clipboard is inaccessible gracefully
            
        # Schedule next poll in 500 ms without blocking the main event loop
        self.root.after(500, self.poll_clipboard)

    def update_ui(self):
        self.listbox.delete(0, tk.END)
        for idx, item in enumerate(self.clipboard_history):
            # Show a snippet of the text to avoid rendering huge lines in the listbox
            display_text = item.replace('\n', ' ')
            if len(display_text) > 80:
                display_text = display_text[:77] + "..."
            self.listbox.insert(tk.END, f"[{idx + 1}]  {display_text}")

    def copy_to_clipboard(self, event):
        selection = self.listbox.curselection()
        if selection:
            index = selection[0]
            if index < len(self.clipboard_history):
                selected_text = self.clipboard_history[index]
                pyperclip.copy(selected_text)
                self.last_clip = selected_text # Prevent immediate re-adding
                print(f"Copied index {index + 1} back to clipboard")

def main():
    root = tk.Tk()
    app = ClipboardManager(root)
    # Handle graceful exit
    root.protocol("WM_DELETE_WINDOW", root.destroy)
    root.mainloop()

if __name__ == "__main__":
    main()
