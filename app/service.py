# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#                                Author: RR                                     #
#                                Software Architect                             #
#                                Pilatewaveai                                   #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

import os
import json
import threading
import queue
import time
import logging
import hashlib
import re
import subprocess
from collections import deque
import pyperclip

try:
    from cryptography.fernet import Fernet
except ImportError:
    logging.error("cryptography package is missing. Install with: pip install cryptography")
    raise

logger = logging.getLogger(__name__)

class ClipboardService:
    def __init__(self, update_queue: queue.Queue, history_limit: int = 10, max_clip_size: int = 1024 * 1024):
        self.update_queue = update_queue
        self.history_limit = history_limit
        self.max_clip_size = max_clip_size
        self.history = deque(maxlen=history_limit)
        
        self._key = Fernet.generate_key()
        self._cipher = Fernet(self._key)
        
        self.dlp_patterns = {
            "AWS_KEY": re.compile(r'(?<![A-Z0-9])[A-Z0-9]{20}(?![A-Z0-9])'),
            "SSH_PRIVATE_KEY": re.compile(r'-----BEGIN (RSA|OPENSSH|DSA|EC|PGP) PRIVATE KEY-----'),
            "JWT_TOKEN": re.compile(r'eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*'),
            "KUBECONFIG": re.compile(r'client-certificate-data:\s*[A-Za-z0-9+/=]+'),
            "CREDIT_CARD": re.compile(r'\b(?:\d[ -]*?){13,16}\b')
        }
        
        self.multi_paste_buffer = deque()
        self._running = False
        self._thread = None
        self._last_clip_hash = None
        self.is_paused = False
        self.templates = []
        
        self._load_templates()

    def _load_templates(self):
        # We store templates securely locally. Users can add JSON templates manually.
        template_file = os.path.expanduser("~/.config/myclipboard/templates.json")
        if not os.path.exists(os.path.dirname(template_file)):
            os.makedirs(os.path.dirname(template_file), exist_ok=True)
            
        if not os.path.exists(template_file):
            default_templates = [
                {"title": "Weekly Update Template", "content": "Hi Team,\n\nHere is my update:\n- Done:\n- Blockers:\n- Next:\n\nThanks,"},
                {"title": "Zoom Meeting Link", "content": "Join Zoom Meeting\nhttps://zoom.us/j/1234567890\nPasscode: 123456"},
                {"title": "Reject Email (Polite)", "content": "Thank you for reaching out. Unfortunately, we are not able to proceed at this time."}
            ]
            with open(template_file, "w") as f:
                json.dump(default_templates, f, indent=4)
                
        try:
            with open(template_file, "r") as f:
                self.templates = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load templates: {e}")

    def get_templates(self):
        return self.templates

    def restore_template(self, index: int):
        if 0 <= index < len(self.templates):
            self.copy_to_clipboard(self.templates[index]["content"])

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        logger.info(f"Clipboard recording paused: {self.is_paused}")

    def start(self):
        if self._running: return
        self._running = True
        self._thread = threading.Thread(target=self._observe_clipboard, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread: self._thread.join(timeout=2.0)
        self.clear_memory()

    def clear_memory(self):
        self._key = b"*" * 44
        self._cipher = None
        while self.history: self.history.pop()
        self._last_clip_hash = None

    def _get_hash(self, text: str) -> str:
        return hashlib.sha256(text.encode('utf-8', errors='ignore')).hexdigest() if text else None

    def _is_sensitive_or_invalid(self, text: str) -> bool:
        if not text or len(text) < 3: return True
        if 8 <= len(text) <= 32 and " " not in text:
            if any(c.isupper() for c in text) and any(c.islower() for c in text) and any(c.isdigit() for c in text) and any(not c.isalnum() for c in text):
                return True
        return False

    def _mask_sensitive_data(self, text: str) -> str:
        masked_text = text
        for label, pattern in self.dlp_patterns.items():
            masked_text = pattern.sub(f"[*** MASKED {label} ***]", masked_text)
        return masked_text

    def _push_update_to_ui(self):
        display_list = []
        for encrypted_item in self.history:
            try:
                plaintext = self._cipher.decrypt(encrypted_item).decode('utf-8', errors='ignore')
                display_text = self._mask_sensitive_data(plaintext.replace('\n', ' '))
                if len(display_text) > 80: display_text = display_text[:77] + "..."
                display_list.append(display_text)
                del plaintext
            except Exception:
                display_list.append("[Encrypted Data]")
        self.update_queue.put({"type": "new_clip", "data": display_list})

    def add_external_clip(self, text: str):
        if not text or len(text.encode('utf-8', errors='ignore')) > self.max_clip_size: return
        if not self._is_sensitive_or_invalid(text):
            current_hash = self._get_hash(text)
            if self._last_clip_hash == current_hash: return
            encrypted_clip = self._cipher.encrypt(text.encode('utf-8'))
            self.history.appendleft(encrypted_clip)
            self._push_update_to_ui()
            self.copy_to_clipboard(text)

    def _is_terminal_or_vault_active(self):
        # Native OS active window polling
        try:
            if os.uname().sysname == "Darwin":
                # MacOS active window polling via AppleScript
                cmd = ['osascript', '-e', 'tell application "System Events" to get name of first process whose frontmost is true']
                output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
                window_name = output.decode('utf-8').strip().lower()
            else:
                # Linux active window polling via xdotool
                output = subprocess.check_output(['xdotool', 'getactivewindow', 'getwindowname'], stderr=subprocess.DEVNULL)
                window_name = output.decode('utf-8').lower()

            sensitive_terms = ['terminal', 'iterm', 'warp', 'konsole', 'alacritty', 'kitty', 'ssh', 'vault', 'sudo', 'keepass', '1password', 'bitwarden']
            if any(term in window_name for term in sensitive_terms):
                return True
        except Exception: pass
        return False

    def _observe_clipboard(self):
        while self._running:
            try:
                if self.is_paused or self._is_terminal_or_vault_active():
                    time.sleep(1.0)
                    continue
                    
                current_clip = pyperclip.paste()
                current_hash = self._get_hash(current_clip)
                
                if current_hash != self._last_clip_hash:
                    if len(current_clip.encode('utf-8', errors='ignore')) > self.max_clip_size:
                        self._last_clip_hash = current_hash
                        continue
                    if not self._is_sensitive_or_invalid(current_clip):
                        encrypted_clip = self._cipher.encrypt(current_clip.encode('utf-8'))
                        self.history.appendleft(encrypted_clip)
                        self._push_update_to_ui()
                    self._last_clip_hash = current_hash
            except Exception: pass
            time.sleep(0.5)

    def restore_from_index(self, index: int):
        if 0 <= index < len(self.history):
            try:
                encrypted_item = self.history[index]
                plaintext = self._cipher.decrypt(encrypted_item).decode('utf-8', errors='ignore')
                self.copy_to_clipboard(plaintext)
                del plaintext
            except Exception: pass

    def queue_multi_paste(self, indices: list):
        self.multi_paste_buffer.clear()
        for idx in indices:
            if 0 <= idx < len(self.history):
                self.multi_paste_buffer.append(self.history[idx])

    def pop_multi_paste(self):
        if self.multi_paste_buffer:
            try:
                encrypted_item = self.multi_paste_buffer.popleft()
                plaintext = self._cipher.decrypt(encrypted_item).decode('utf-8', errors='ignore')
                self.copy_to_clipboard(plaintext)
                del plaintext
            except Exception: pass

    def transform_item(self, index: int, transform_type: str):
        if 0 <= index < len(self.history):
            try:
                encrypted_item = self.history[index]
                plaintext = self._cipher.decrypt(encrypted_item).decode('utf-8', errors='ignore')
                transformed_text = plaintext
                
                if transform_type == "json":
                    try:
                        parsed = json.loads(plaintext)
                        transformed_text = json.dumps(parsed, indent=4)
                    except json.JSONDecodeError: del plaintext; return
                elif transform_type == "camel":
                    parts = plaintext.replace('_', ' ').replace('-', ' ').split()
                    if parts: transformed_text = parts[0].lower() + ''.join(word.capitalize() for word in parts[1:])
                elif transform_type == "snake":
                    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', plaintext)
                    transformed_text = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
                    transformed_text = transformed_text.replace('-', '_').replace(' ', '_')
                elif transform_type == "base64":
                    import base64
                    transformed_text = base64.b64encode(plaintext.encode('utf-8')).decode('utf-8')
                elif transform_type == "base64_decode":
                    import base64
                    try: transformed_text = base64.b64decode(plaintext.strip()).decode('utf-8')
                    except Exception: del plaintext; return

                self.add_external_clip(transformed_text)
                del plaintext; del transformed_text
            except Exception: pass

    def copy_to_clipboard(self, text: str):
        try:
            pyperclip.copy(text)
            self._last_clip_hash = self._get_hash(text)
        except Exception: pass
