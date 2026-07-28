import logging
from concurrent.futures import ThreadPoolExecutor

from config import SCRATCHPAD_PATH, MAX_PARALLEL_WORKERS, MAX_REVISIONS, MAX_REPLANS
from scratchpad import Scratchpad
from orchestrator import plan
from worker import run_worker
from verifier import verify

logging.getLogger("LiteLLM").setLevel(logging.ERROR)


def run_subtask(pad, sid):
    result = ""
    for _ in range(MAX_REVISIONS + 1):
        ctx = pad.context_for(sid)
        result = run_worker(ctx)
        verdict = verify(ctx, result)
        pad.log("verifier", f"[{sid}] pass={verdict.get('pass')} {verdict.get('feedback', '')}")
        if verdict.get("pass"):
            pad.update(sid, status="pass", result=result, summary=verdict.get("summary"))
            return True
        with pad.lock:
            sub_now = pad.state["plan"][sid]
            sub_now["feedback"].append(verdict.get("feedback", ""))
            pad.update(sid, feedback=sub_now["feedback"], result=result)
    pad.update(sid, status="fail", result=result)
    return False


def main():
    task = input("Task> ").strip()
    if not task:
        return
    pad = Scratchpad(SCRATCHPAD_PATH)
    pad.set_task(task)

    for attempt in range(MAX_REPLANS + 1):
        subtasks = plan(task)
        pad.set_plan(subtasks)
        pad.log("orchestrator", f"Planned {len(subtasks)} subtasks (attempt {attempt})")

        n = len(subtasks)
        done, failed = set(), False
        with ThreadPoolExecutor(max_workers=MAX_PARALLEL_WORKERS) as ex:
            while len(done) < n and not failed:
                batch = [
                    i for i, s in enumerate(pad.state["plan"])
                    if s["status"] == "pending" and all(int(d) in done for d in s["deps"])
                ]
                if not batch:
                    failed = True  # nothing runnable -> unmet deps / cycle
                    break
                for i, ok in ex.map(lambda i: (i, run_subtask(pad, i)), batch):
                    if ok:
                        done.add(i)
                    else:
                        failed = True

        if len(done) == n:
            print(f"\nAll {n} subtasks passed. Scratchpad: {SCRATCHPAD_PATH}")
            return
        pad.log("orchestrator", "Some subtasks failed - replanning")

    print("\nGave up after exhausting replans. See scratchpad for details.")


if __name__ == "__main__":
    main()
