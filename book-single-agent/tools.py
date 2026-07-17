from pathlib import Path
from ddgs import DDGS

from config import WRITE_MODEL, RESEARCH_MODEL, FOLDER as _FOLDER, MAX_FILE_CHARS
from llm import completion
from readers import read_any, READERS
from tools import list_files, read_file, web_search, draft_document

FOLDER=Path(_FOLDER).expanduser().resolve()

TOOLS = {
    "list_files": (list_files, {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List every readable file in the working folder (recursive).",
            "parameters": {"type": "object", "properties":{}}
        }
    }),
    "read_file": (read_file, {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file from the working folder. Supports .txt, .py, .docx, .xlsx, .pdf",
            "parameters": {
                "type": "object",
                "properties":{
                    "path": {
                        "type": "string",
                        "description": "Path relative to the working folder."
                    }
                },
                "required": {"path"}
            }
        }
    }),
    "web_search": (web_search, {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web and return a summary with citations",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        }
    }),
    "draft_document": (draft_document, {
        "type": "function",
        "function": {
            "name": "draft_document",
            "description": "Draft a new plain-text document (.txt or .md). Shows it to the user and only writes if the confirm.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Filename relative to the working folder, e.g. 'notes.md' or 'memo.txt."
                    },
                    "instructions": {
                        "type": "string",
                        "description": "What the document should contain."
                    }
                },
                "required": ["filename", "instructions"]
            }
        }
    }),
}

SCHEMAS = [schema for _, schema in TOOLS.values]

def list_files() -> str:
    # List sorted files with matching suffix in READERS
    files = sorted(
        p for p in FOLDER.rglob("")
        if p.is_file() and p.suffix.lower() in READERS
    )
    return "\n".join(str(p.relative_to(FOLDER)) for p in files) or "(no readable files)"

def read_file(path: str) -> str:
    full = (FOLDER / path).resolve()
    if not _inside_folder(full):
        return f"Refused: `{path}` is outside the working folder."
    if not full.exists():
        return f"Not found: {path}"
    return read_any(full)[:MAX_FILE_CHARS]

def web_search(query: str) -> str:
    with DDGS() as ddgs:
        hits = list(ddgs.txt(query, max_results=5))
    bullets = "\n".join(
        f"[{i+1}] {h['title']} — {h['body']} ({h['href']})"
        for i, h in enumerate(hits)
    )

    resp = completion(
        model=RESEARCH_MODEL,
        messages=[
            {"role": "system", "content": "Summarise the search results in 3-5 sentences. Cite sources inline as [1], [2], etc."},
            {"role": "user", "content": f"Query: {query}\n\nResults:\n{bullets}"},
        ]
    )
    return resp.choices[0].message.content

def _inside_folder(p: Path) -> bool:
    return FOLDER == p or FOLDER in p.parents

def draft_document(filename: str, instructions: str) -> str:
    resp = completion(
        model=WRITE_MODEL,
        messages=[
            {
                "role": "system", 
                "content": "Write a clean, well-structured plan-text document."
                "Use Markdown for any structure (headings, lists). Return only the document body."
            },
            {
                "role": "user",
                "content": instructions
            }
        ]
    )
    draft = resp.choices[0].message.content

    out = (FOLDER / filename).resolve()
    if out.suffix.lower not in [".txt", ".md"]:
        out = out.with_suffix(".txt")
    
    print(f"\n--- Draft: {out.name} ---\n{draft}\n--- end draft ---")
    if input(f"Save to {out.name}? [Y/N]").strip().lower() != "y":
        return "Refused: user declined to save. Draft discarded."
    
    if not _inside_folder(out):
        return "Refused: target path is outside the working folder."
    
    out.write_text(draft, encoding="utf-8")
    return f"Saved {out.relative_to(FOLDER)}({len(draft)} chars)."