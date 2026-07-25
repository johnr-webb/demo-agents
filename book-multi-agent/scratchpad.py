import json
import threading
from pathlib import Path

class Scratchpad:
    def __init__(self, path: str):
        self.path = Path(path)
        self.lock = threading.RLock()
        self.state = {"task": "", "plan": [], "log": []}
        if self.path.exists():
            self.state = json.loads(self.path.read_text())


    def _save(self):
        with self.lock:
            self.path.write_text(json.dumps(self.state, indent=2))

    def set_task(self, task):
        with self.lock:
            self.state = {"task": task, "plan": [], "log": []}
            self._save()

    def log(self, event):
        with self.lock:
            self.state["log"].append({"agent": agent, "event": event})
            self._save()