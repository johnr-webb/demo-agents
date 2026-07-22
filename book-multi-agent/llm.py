import json
from litellm import completion

# The capability you withhold is as much a part of an agent's
# behavior as the capability you grant
# Tools default to None
def chat(model, system, messages, tools=None):
    response = completion(
        model=model,
        messages=[{"role": "system", "content": system}] + messages,
        tools=tools,
    )
    return response.choices[0].message

def run_agent(model, system, user_msg, tools, handlers, max_steps=15):
    messages = [{"role": "user", "content": user_msg}]
    total_tool_calls = 0
    for _ in range(max_steps):
        msg = chat(model, system, messages, tools)
        assistant = {"role": "assistant", "content": msg.content or ""}

        if msg.tool_calls:
            assistant["tool_calls"] = [
                {
                    "id": tc.id, 
                    "type": "function", 
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in msg.tool_calls
            ]
        messages.append(assistant)

        if not msg.tool_calls:
            return msg.content or ""

        for tc in msg.tool_calls:
            total_tool_calls += 1
            try:
                result = handlers[tc.function.name](**json.loads(tc.function.arguments))
            except Exception as e:
                result = f"Tool error {e}"
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": str(result)})
    return f"(Max steps reached without final answer) Total tool calls: {total_tool_calls}"