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