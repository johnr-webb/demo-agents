import subprocess
import threading
from pathlib import Path
from config import Workspace

WORKSPACE_DIR = Path(WORKSPACE).resolve()
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)

def _safe(path: str) -> Path:
    p = (WORKSPACE_DIR / path).resolve()
    if not str(p).startswith(str(WORKSPACE_DIR)):
        raise ValueError(f"Path {path} escapes the workspace")
    return p

def read_file(path: str) -> str:
    return _safe(path).read_text()

def write_file(path: str, content:str) -> str:
    p = _safe(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return f"Wrote {len(content)} chars to {path}"

def list_files() -> str:
    files = sorted(str(p.relative_to(WORKSPACE_DIR)) for p in WORKSPACE_DIR.rglob("*") if p.is_file())
    return "\n".join(files) or "(empty)"

RISKY = ("rm", "sudo", "curl", "wget", "pip install", "npm install", "git push", "git reset", "chmod", "mv")

def run_shell(command: str) -> str:
    if any(command.strip().startswith(p) for p in RISKY):
        with _hitl_lock:
            print(f"\n [HITL] Worker wants to run: {command}")
            if input(" Approve? [Y/N]:").strip().lower() != "y":
                return "DENIED by human"
    proc = subprocess.run(command, shell=True, cwd=WORKSPACE_DIR, capture_output=True, text=True, timeout=120)
    return f"exit={proc.returncode}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"

_hitl_lock = threading.Lock()

def _tool(name, desc, props, required):
    return {
        "type": "function", 
        "function": {
            "name": name, 
            "description": desc,
            "parameters": {
                "type": "object",
                "properties": props,
                "required": required
            }
        }
    }

TOOLS = [
    _tool("read_file", "Read a file from the workspace.", {"path": {"type": "string"}}, ["path"]),
    _tool("write_file", "Write (overwrite) a file in the workspace.", {"path": {"type": "string"}, "content": {"type": "string"}},["path", "content"]),
    _tool("list_files", "List every file in the workspace.", {}, []),
    _tool("run_shell", "Run a shell command in the workspace. Risky commands require human approval.",{"command": {"type": "string"}}, ["command"])
]

HANDLERS = {
    "read_file": read_file,
    "write_file": write_file,
    "list_files": list_files,
    "run_shell": run_shell
}

READ_ONLY_TOOLS = [
    t for t in TOOLS if t["function"]["name"] in ("read_file", "list_files")
]

READ_ONLY_HANDLERS = {
    k: v for k, v in HANDLERS.items() if k in ("read_file", "list_files")
}