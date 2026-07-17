import sys
import threading
import time
from litellm import completion as _completion

def completion(*args, **kwargs):
    result, error = {}, {}

    def target():
        try:
            result["value"] = _completion(*args, **kwargs)
        except Exception as e:
            error["value"] = e
    
    thread = threading.Thread(target=target)
    thread.start()
    start = time.monotonic()
    elapsed = 1
    while thread.is_alive():
        elapsed = int(time.monotonic() - start) + 1
        sys.stdout.write(f"\rThinking {elapsed}s...")
        sys.stdout.flush()
        thread.join(timeout=1.0)
    sys.stdout.write(f"\rThought for {elapsed}s" + " "*10 + "\n")
    sys.stdout.flush()
    
    if "value" in error:
        raise error["value"]
    return result["value"]

