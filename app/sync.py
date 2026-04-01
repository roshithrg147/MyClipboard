import os
import json
import time
import threading
import logging
import base64
import requests
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)

class SyncService:
    def __init__(self, update_queue):
        self.update_queue = update_queue
        self.enabled = False
        self.secret_key = None
        self._cipher = None
        self.relay_url = "https://httpbin.org/post"  # Default mock relay for testing
        self.device_id = os.uname().nodename
        self.last_sync_time = 0
        self._running = False
        self._sync_thread = None
        self.status = "Disconnected"

    def set_config(self, enabled, secret_key):
        self.enabled = enabled
        if secret_key:
            try:
                # Derive a Fernet-compatible key from the user's secret
                salt = b'myclipboard_salt' # In production, use a unique per-user salt
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=100000,
                )
                key = base64.urlsafe_b64encode(kdf.derive(secret_key.encode()))
                self._cipher = Fernet(key)
                self.secret_key = secret_key
                self.status = "Connected" if self.enabled else "Disconnected"
            except Exception as e:
                logger.error(f"Sync Key Derivation Error: {e}")
                self.status = "Error"
        else:
            self._cipher = None
            self.status = "Disconnected"
        
        if self.enabled and not self._running:
            self.start()
        elif not self.enabled and self._running:
            self.stop()

    def start(self):
        if self._running: return
        self._running = True
        self._sync_thread = threading.Thread(target=self._periodic_pull, daemon=True)
        self._sync_thread.start()

    def stop(self):
        self._running = False

    def push(self, text):
        if not self.enabled or not self._cipher:
            return

        def _async_push():
            try:
                encrypted_data = self._cipher.encrypt(text.encode())
                payload = {
                    "device_id": self.device_id,
                    "blob": encrypted_data.decode(),
                    "timestamp": time.time()
                }
                # Using a simple POST relay (mocked with httpbin for now)
                requests.post(self.relay_url, json=payload, timeout=5)
                logger.info("Sync push successful")
            except Exception as e:
                logger.error(f"Sync Push Error: {e}")
                self.status = "Error"

        threading.Thread(target=_async_push, daemon=True).start()

    def _periodic_pull(self):
        while self._running:
            if self.enabled and self._cipher:
                try:
                    # In a real ZK-Relay, we would fetch the latest blob for this user/account
                    # Mocking pull for now as it needs a real relay state
                    pass
                except Exception as e:
                    logger.error(f"Sync Pull Error: {e}")
            time.sleep(60) # Pull every minute

    def get_status(self):
        return self.status
