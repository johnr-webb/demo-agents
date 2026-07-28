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


    def save(self):
        with self.lock:
            self.path.write_text(json.dumps(self.state, indent=2))

    def set_task(self, task):
        with self.lock:
            self.state = {"task": task, "plan": [], "log": []}
            self.save()

    def log(self, agent, event):
        with self.lock:
            self.state["log"].append({"agent": agent, "event": event})
            self.save()

    def set_plan(self, subtasks: list[dict]):
        with self.lock:
            self.state["plan"] = [
                {
                    "id": s["id"],
                    "description": s["description"],
                    "deps": list(s.get("deps", [])),
                    "status": "pending",
                    "result": None,
                    "summary": None,
                    "feedback": []
                }
                for s in subtasks
            ]
            self.save()

    def update(self, sid, **fields):
        with self.lock:
            self.state["plan"][sid].update(fields)
            self.save()

    def context_for(self, sid):
        with self.lock:
            sub = self.state["plan"][sid]
            deps = [self.state["plan"][int(d)] for d in sub["deps"]]
            completed = [f"- [{d['id']}] {d['description']} -> {d['summary']}" for d in deps if d["status"] == "pass"]
            context = {
                "task": self.state["task"],
                "completed": completed,
                "subtask": sub["description"],
                "feedback": list(sub.get("feedback", []))
            }
            return context