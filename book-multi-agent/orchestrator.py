import json
from config import MODELS
from llm import chat

SYSTEM = """
You are the Orchestrator in a multi-agent coding system.

Decompose the user's coding task into a small DAG of subtasks. Each subtask
is handed off to a Worker agent (which can read/write files and run shell
commands inside a workspace directory). Subtasks with no shared dependencies
will be executed in parallel - exploit this when it is safe.

Rules:
- 2-6 subtasks total. Each must be independently executable and self-contained.
- One concrete deliverable per subtask (e.g. "create file X with Y", "write
tests for Z and run them"). Avoid vague subtasks like "desing the system".
- Mark "deps" honestly: only list ids that "must" finish before this one can
start. If two subtasks could run safely at the same time, give them no shared
deps so the parallelize.

Reply with JSON only, in this exact shape:
{
  "subtasks": [
    {
      "id": "0",
      "description": "Describe the subtask here",
      "deps": []
    },
    {
      "id": "1",
      "description": "...",
      "deps": ["0"]
    },
    {
      "id": "2",
      "description": "...",
      "deps": ["0"]
    }
    {
      "id": "3",
      "description": "...",
      "deps": ["1", "2"]
    }
  ]
}
Id must be consecutive integers starting at 0.
"""

def _json(raw):
    raw = (raw or "").strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(raw)

def plan(task):
    msg = chat(MODELS["orchestrator"], SYSTEM, [{"role": "user", "content": task}])
    return _json(msg.content)["subtasks"]