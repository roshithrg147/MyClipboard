import threading
import queue
import time
import logging
from collections import deque
import pyperclip

logger = logging.getLogger(__name__)

class ClipboardService:
    def __init__(self, update_queue: queue.Queue, history_limit: int = 10, max_clip_size: int = 1024 * 1024):
        self.update_queue = update_queue
        self.history_limit = history_limit
        self.max_clip_size = max_clip_size
        self.history = deque(maxlen=history_limit)
        
        self._running = False
        self._thread = None
        self._last_clip = None

    def start(self):
        if self._running:
            return
        logger.info("Starting ClipboardService observer thread.")
        self._running = True
        self._thread = threading.Thread(target=self._observe_clipboard, daemon=True)
        self._thread.start()

    def stop(self):
        logger.info("Stopping ClipboardService observer thread.")
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        self.clear_memory()

    def clear_memory(self):
        logger.info("Clearing sensitive clipboard history from memory.")
        # Overwrite variables to ensure memory is securely cleared
        for i in range(len(self.history)):
            history_len = len(self.history[i])
            self.history[i] = "*" * history_len
        
        while self.history:
            self.history.pop()
            
        if self._last_clip:
            self._last_clip = "*" * len(self._last_clip)
        self._last_clip = None

    def _is_sensitive_or_invalid(self, text: str) -> bool:
        if not text:
            return True
        if len(text) < 3:
            return True
        
        # Super basic heuristic for password-like strings: 
        # often 8-32 chars, mix of upper/lower/symbols, no spaces
        if 8 <= len(text) <= 32 and " " not in text:
            has_upper = any(c.isupper() for c in text)
            has_lower = any(c.islower() for c in text)
            has_digit = any(c.isdigit() for c in text)
            has_symbol = any(not c.isalnum() for c in text)
            if has_upper and has_lower and has_digit and has_symbol:
                logger.warning("Sensitive data detected (password heuristic). Ignoring.")
                return True
                
        return False

    def _observe_clipboard(self):
        while self._running:
            try:
                current_clip = pyperclip.paste()
                
                if current_clip != self._last_clip:
                    # Size check
                    if len(current_clip.encode('utf-8', errors='ignore')) > self.max_clip_size:
                        logger.warning(f"Clipboard content exceeded MAX_CLIP_SIZE ({self.max_clip_size} bytes). Ignoring.")
                        self._last_clip = current_clip # prevent spamming warning
                        continue

                    # Filter sensitive/invalid
                    if not self._is_sensitive_or_invalid(current_clip):
                        self.history.appendleft(current_clip)
                        # Push an event to the Queue for the UI consumer
                        self.update_queue.put({"type": "new_clip", "data": list(self.history)})
                        logger.info("New clipboard item processed.")
                    
                    self._last_clip = current_clip

            except pyperclip.PyperclipException as e:
                logger.error(f"Pyperclip error accessing clipboard: {e}")
            except Exception as e:
                logger.error(f"Unexpected error in observer thread: {e}")
                
            time.sleep(0.5)

    def copy_to_clipboard(self, text: str):
        try:
            pyperclip.copy(text)
            self._last_clip = text # prevent observer from re-adding it immediately
            logger.info("Restored historical item to active clipboard.")
        except Exception as e:
            logger.error(f"Failed to copy to clipboard: {e}")
