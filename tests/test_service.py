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
    service.add_external_clip("secret_cookie_token")
    assert len(service.history) > 0
    assert service._last_clip_hash is not None
    
    service.clear_memory()
    
    assert len(service.history) == 0
    assert service._last_clip_hash is None
    assert service._cipher is None # Memory wiped
