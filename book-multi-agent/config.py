import os
from dotenv import load_dotenv


load_dotenv()

MODELS = {
    "orchestrator": os.getenv("ORCHESTRATOR_MODEL", "anthropic/claude-opus-4-7"),
    "worker": os.getenv("WORKER_MODEL", "anthropic/claude-sonnet-4-6"),
    "verifier": os.getenv("VERIFIER_MODEL", "anthropic/claude-sonnet-4-6")
}

WORKSPACE = os.getenv("WORKSPACE", "./workspace")
SCRATCHPAD_PATH = os.getenv("SCRATCHPAD", "./scratchpad.json")
