import pytest
import threading
import time
from collections import deque
from app.service import ClipboardService
import queue
import gc

def test_concurrency_race_condition():
    """
    Test for race conditions in history deque access.
    The CTO audit identified that _observe_clipboard (bg thread) and _push_update_to_ui (UI thread)
    access self.history without sufficient protection.
    """
    update_queue = queue.Queue()
    service = ClipboardService(update_queue=update_queue, history_limit=100)
    
    # Simulate rapid background updates
    def bg_updates():
        for i in range(1000):
            service.add_external_clip(f"Clip {i}")
            time.sleep(0.001)

    # Simulate rapid UI-triggered reads/decryptions
    def ui_reads():
        for _ in range(100):
            service._push_update_to_ui()
            time.sleep(0.01)

    t1 = threading.Thread(target=bg_updates)
    t2 = threading.Thread(target=ui_reads)
    
    t1.start()
    t2.start()
    
    t1.join()
    t2.join()

def test_salt_randomization():
    """
    Test that salts are unique per config.
    """
    import os
    import json
    import base64
    from app.sync import SyncService, CONFIG_PATH
    
    # Backup existing config
    backup = None
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                backup = f.read()
            os.remove(CONFIG_PATH)
        except: pass

    try:
        s1 = SyncService(queue.Queue())
        salt1 = s1._get_or_create_salt()
        
        # New instance should read same salt if file exists
        s2 = SyncService(queue.Queue())
        salt2 = s2._get_or_create_salt()
        assert salt1 == salt2

        # If file is gone, new salt should be different
        if os.path.exists(CONFIG_PATH):
            os.remove(CONFIG_PATH)
        s3 = SyncService(queue.Queue())
        salt3 = s3._get_or_create_salt()
        assert salt1 != salt3
    finally:
        if backup:
            os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
            with open(CONFIG_PATH, "w") as f:
                f.write(backup)
        elif os.path.exists(CONFIG_PATH):
            os.remove(CONFIG_PATH)

def test_entropy_sensitive_detection():
    """
    Test the new entropy-based sensitive data detection.
    """
    update_queue = queue.Queue()
    service = ClipboardService(update_queue=update_queue)
    
    # Normal text should not be sensitive
    assert not service._is_sensitive_or_invalid("Hello world, this is a test.")
    
    # High entropy strings (simulated keys) should be sensitive
    assert service._is_sensitive_or_invalid("4f8a2b9c1d0e3f5g7h9i2j4k6l8m0n2o")
    assert service._is_sensitive_or_invalid("zK9!pL2#mN5*qR8@tV1&xY4^")

def test_memory_leakage_clear_memory():
    """
    Test if clear_memory properly wipes sensitive data.
    """
    update_queue = queue.Queue()
    service = ClipboardService(update_queue=update_queue)
    
    secret_text = "VERY_SENSITIVE_SECRET_12345"
    service.add_external_clip(secret_text)
    
    # Verify it's there
    found = False
    with service.lock:
        for item in service.history:
            if secret_text in service._cipher.decrypt(item).decode():
                found = True
    assert found
    
    service.clear_memory()
    
    assert len(service.history) == 0
    assert service._cipher is None
    
    gc.collect()
    
    assert service._last_clip_hash is None
    if hasattr(service, 'ai_insights'):
        assert len(service.ai_insights) == 0

def test_wayland_detection_mock():
    """
    Verify Wayland detection logic fallback paths.
    """
    import os
    from app.service import ClipboardService
    import queue
    import subprocess
    from unittest.mock import patch, MagicMock

    update_queue = queue.Queue()
    service = ClipboardService(update_queue=update_queue)

    # Test MacOS path
    with patch('os.uname') as mock_uname:
        mock_uname.return_value.sysname = "Darwin"
        with patch('subprocess.check_output') as mock_cmd:
            mock_cmd.return_value = b"Terminal"
            assert service._is_terminal_or_vault_active() is True

    # Test Linux path - GNOME Wayland (gdbus)
    with patch('os.uname') as mock_uname:
        mock_uname.return_value.sysname = "Linux"
        # Simulate gdbus success
        def mock_run(cmd, **kwargs):
            if cmd[0] == 'gdbus':
                return b"('Some Private Vault',)"
            raise subprocess.CalledProcessError(1, cmd)
        
        with patch('subprocess.check_output', side_effect=mock_run):
            assert service._is_terminal_or_vault_active() is True

    # Test Linux path - Fallback to xdotool
    with patch('os.uname') as mock_uname:
        mock_uname.return_value.sysname = "Linux"
        def mock_run_fallback(cmd, **kwargs):
            if cmd[0] == 'xdotool':
                return b"gnome-terminal"
            raise subprocess.CalledProcessError(1, cmd)
            
        with patch('subprocess.check_output', side_effect=mock_run_fallback):
            assert service._is_terminal_or_vault_active() is True

if __name__ == "__main__":
    pytest.main([__file__])
