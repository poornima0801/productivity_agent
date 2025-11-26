import json
from openai import OpenAI

client = OpenAI()

# ------------------------
# Simple JSON-based storage
# ------------------------
TASK_FILE = "tasks.json"

def load_tasks():
    try:
        with open(TASK_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_tasks(tasks):
    with open(TASK_FILE, "w") as f:
        json.dump(tasks, f, indent=2)


# ------------------------
# Tools (Agent Actions)
# ------------------------
def add_task(task_desc):
    tasks = load_tasks()
    task_id = len(tasks) + 1
    tasks.append({"id": task_id, "task": task_desc, "status": "pending"})
    save_tasks(tasks)
    return f"Task added: {task_desc}"

def complete_task(task_id):
    tasks = load_tasks()
    for t in tasks:
        if t["id"] == task_id:
            t["status"] = "completed"
            save_tasks(tasks)
            return f"Marked task {task_id} as completed."
    return "Task not found."

def list_tasks():
    tasks = load_tasks()
    if not tasks:
        return "You have no tasks."
    result = "Here are your tasks:\n"
    for t in tasks:
        result += f"{t['id']}. {t['task']} — {t['status']}\n"
    return result


# ------------------------
# Intent Classifier
# ------------------------
def classify_intent(message):
    msg = message.lower()

    if "add task" in msg or "remember" in msg or "todo" in msg:
        return "add_task"
    if "complete" in msg or "done" in msg or "finish" in msg:
        return "complete_task"
    if "list" in msg or "show tasks" in msg:
        return "list_tasks"

    return "chat"


# ------------------------
# Main Agent
# ------------------------
def ai_agent(user_input):

    intent = classify_intent(user_input)

    tool_output = None

    # route to correct tool
    if intent == "add_task":
        task_desc = user_input.replace("add task", "").replace("remember", "")
        tool_output = add_task(task_desc.strip())

    elif intent == "complete_task":
        nums = [int(s) for s in user_input.split() if s.isdigit()]
        if nums:
            tool_output = complete_task(nums[0])
        else:
            tool_output = "Which task number?"

    elif intent == "list_tasks":
        tool_output = list_tasks()

    # system prompt
    system_msg = f"""
    You are a helpful productivity AI assistant.
    Intent: {intent}
    Tool output: {tool_output}
    If tool_output exists, you MUST use it in your final answer.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_input}
        ]
    )

    return response.choices[0].message["content"]
