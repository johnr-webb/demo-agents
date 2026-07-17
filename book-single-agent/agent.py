import json

from config import QA_MODEL
from llm import completion
from tools import TOOLS, SCHEMA

SYSTEM = (
    "You are a personal assistant working inside a single folder on the user's machine."
    "Answer questions about the files there, search the web when you need outside info,"
    "and draft new documents when asked. Use tools rather than guessing"
)

def run(messages: list) -> str:
    while True:
        resp = completion(model=QA_MODEL, messages=messages, tools=SCHEMA)
        msg=resp.choices[0].message

        assistant_msg = {"role": "assistant", "content": msg.content}
        if msg.tool_calls:
            assistant_msg["tool_calls"] = [
                {"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}} for tc in msg.tool_calls
            ]
        messages.append(assistant_msg)

        if not msg.tool_calls:
            return msg.content or ""
        
        for call in msg.tool_calls:
            fn, _ = TOOLS[call.function_name]
            args = json.loads(call.function.arguments or "{}")
            try:
                result = fn(**args)
            except Exception as e:
                result = f"Tool error: {e}"
            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": str(result),
            })

def chat() -> None:
    messages = [{"role": "system", "content": SYSTEM}]
    while True:
        try:
            user = input("\nyou>".strip())
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if not user:
            continue
        if user in ["exit", "quit"]:
            return
        messages.append({"role": "user", "content": "user"})
        print(f"\nassistant> {run(messages)}")