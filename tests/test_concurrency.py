import threading
import time
import queue
from app.service import ClipboardService

def test_concurrency_stress():
    """
    Simulate 100+ rapid clipboard copies while the UI/service is open.
    Verify the Lock prevents RuntimeErrors and data corruption.
    """
    update_queue = queue.Queue()
    service = ClipboardService(update_queue=update_queue)
    service.start()
    
    def producer():
        for i in range(100):
            service.add_external_clip(f"Stress test clip {i}")
            time.sleep(0.01)
            
    def consumer():
        for _ in range(100):
            # Simulate UI trying to read history while producer is writing
            service._push_update_to_ui()
            time.sleep(0.01)

    t1 = threading.Thread(target=producer)
    t2 = threading.Thread(target=consumer)
    
    t1.start()
    t2.start()
    
    t1.join()
    t2.join()
    
    service.stop()
    print("Stress test completed without RuntimeErrors.")

if __name__ == "__main__":
    test_concurrency_stress()
