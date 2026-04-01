# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#                                Author: RR                                     #
#                                Software Architect                             #
#                                Pilatewaveai                                   #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

import pytest
import queue
from app.service import ClipboardService

@pytest.fixture
def service():
    q = queue.Queue()
    svc = ClipboardService(update_queue=q, history_limit=3, max_clip_size=1024)
    yield svc
    # Clean up
    svc.stop()

def test_sensitive_filter(service):
    assert service._is_sensitive_or_invalid("ab") == True  # Too short
    assert service._is_sensitive_or_invalid("A1") == True  # Too short
    assert service._is_sensitive_or_invalid("P@ssw0rd123!") == True # Matches typical password pattern
    assert service._is_sensitive_or_invalid("This is a genuinely valid clip test.") == False

def test_history_deque_limit_and_rotation(service):
    service.add_external_clip("test1")
    service.add_external_clip("test2")
    service.add_external_clip("test3")
    service.add_external_clip("test4")
    
    assert len(service.history) == 3 # Should not exceed history_limit=3
    # Check if we can decrypt the first item to "test4"
    plaintext = service._cipher.decrypt(service.history[0]).decode('utf-8')
    assert plaintext == "test4"

def test_clear_memory(service):
    service.ai_enabled = True
    service.add_external_clip("secret_cookie_token")
    service.ai_insights["dummy_hash"] = b"encrypted_insight"
    assert len(service.history) > 0
    assert service._last_clip_hash is not None
    assert len(service.ai_insights) == 1
    
    service.clear_memory()
    
    assert len(service.history) == 0
    assert service._last_clip_hash is None
    assert service._cipher is None # Memory wiped
    assert len(service.ai_insights) == 0

def test_threading_lock(service):
    # This just ensures the lock is present and can be acquired
    assert hasattr(service, 'lock')
    with service.lock:
        service.history.append(b"locked_item")
    assert len(service.history) == 1

def test_transform_json(service):
    service.add_external_clip('{"key": "value"}')
    # service.history[0] is the encrypted item
    service.transform_item(0, "json")
    # New item (transformed) is at index 0, old one at 1
    with service.lock:
        plaintext = service._cipher.decrypt(service.history[0]).decode('utf-8')
        assert '"key": "value"' in plaintext
        assert "    " in plaintext # Indentation from json.dumps

def test_multi_paste(service):
    service.add_external_clip("item1")
    service.add_external_clip("item2")
    service.queue_multi_paste([0, 1])
    assert len(service.multi_paste_buffer) == 2
    
    service.pop_multi_paste()
    # Note: pyperclip might not work in headless tests, but we're testing the buffer logic
    assert len(service.multi_paste_buffer) == 1
