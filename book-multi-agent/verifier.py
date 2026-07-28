import json
from config import MODELS, MAX_AGENT_STEPS
from llm import run_agent
from worker import READ_ONLY_TOOLS, READ_ONLY_HANDLERS

SYSTEM = """You are the Verifier in a multi-agent coding system.
A Worker claims to have completed a subtask. Independently inspect the workspace
(read_file, list_files) to confirm the deliverable actually exists and is correct -
do not take the Worker's word for it.

Reply with JSON only:
{"pass": true|false, "summary": "one line describing what was delivered", "feedback": "what to fix if failing, else empty"}"""

def verify(ctx, result):
    user = (
        f"Overall task: {ctx['task']}\n"
        f"Subtask: {ctx['subtask']}\n\n"
        f"Worker's report:\n{result}\n\n"
        "Verify it against the workspace and reply with the JSON verdict."
    )
    raw = run_agent(MODELS["verifier"], SYSTEM, user, READ_ONLY_TOOLS, READ_ONLY_HANDLERS, MAX_AGENT_STEPS)
    raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(raw)
    except Exception:
        return {"pass": False, "summary": "", "feedback": f"Unparseable verifier output: {raw[:200]}"}
