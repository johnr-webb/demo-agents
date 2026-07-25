

with pad.lock:
    sub_now = pad.state["plan"][sid]
    sub_now["feedback"].append(verdict["feedback"])
    pad.update(sid, feedback=sub_now["feedback"], result=result)