import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Load Gemini API Key
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")

# --- 🛠️ FIX APPLIED HERE ---
# Correct REST endpoint (using stable model name: gemini-2.5-flash)
API_URL = "https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent"


# ------------------------
# Gemini Request Function
# ------------------------
def call_gemini(prompt):
    """
    Makes a REST API call to the Gemini generateContent endpoint.
    """
    if not GEMINI_API_KEY:
        return "❌ ERROR: Missing GOOGLE_API_KEY in .env"

    headers = {"Content-Type": "application/json"}
    params = {"key": GEMINI_API_KEY}

    data = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    response = requests.post(API_URL, headers=headers, params=params, json=data)

    try:
        response.raise_for_status()
    except Exception:
        # Returns the full error response text if status code indicates failure (4xx or 5xx)
        return f"❌ Gemini API Error: {response.text}"

    # Extract the generated text from the successful response
    try:
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]
    except KeyError:
        return "❌ Error: Could not parse response from Gemini."


# ------------------------
# JSON Task Storage
# ------------------------
TASK_FILE = "tasks.json"

def load_tasks():
    """Loads tasks from the tasks.json file."""
    try:
        with open(TASK_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        # Create an empty list if the file doesn't exist
        return []
    except json.JSONDecodeError:
        # Handle case where file is corrupt/empty
        print(f"Warning: {TASK_FILE} is empty or invalid. Starting with empty list.")
        return []

def save_tasks(tasks):
    """Saves the current list of tasks to the tasks.json file."""
    with open(TASK_FILE, "w") as f:
        json.dump(tasks, f, indent=2)


# ------------------------
# Tools (Add, Complete, List Tasks)
# ------------------------
def add_task(task_desc):
    """Adds a new task to the list."""
    tasks = load_tasks()
    # Find the next available ID
    task_id = max([t['id'] for t in tasks], default=0) + 1
    tasks.append({"id": task_id, "task": task_desc, "status": "pending"})
    save_tasks(tasks)
    return f"Task added: {task_desc} (ID: {task_id})"

def complete_task(task_id):
    """Marks a task as completed by ID."""
    tasks = load_tasks()
    try:
        task_id = int(task_id) # Ensure ID is integer
    except ValueError:
        return "Error: Task ID must be a number."
        
    for t in tasks:
        if t["id"] == task_id:
            t["status"] = "completed"
            save_tasks(tasks)
            return f"Marked task {task_id} ('{t['task']}') as completed."
    return f"Task ID {task_id} not found."

def list_tasks():
    """Returns a formatted string of all tasks."""
    tasks = load_tasks()
    if not tasks:
        return "You have no tasks."
    
    result = "Here are your tasks:\n"
    for t in tasks:
        # Use simple status emoji for better readability
        status_icon = "✅" if t['status'] == 'completed' else "⏳"
        result += f"{t['id']}. {status_icon} {t['task']} — {t['status'].upper()}\n"
    return result


# ------------------------
# Intent Classifier
# ------------------------
def classify_intent(message):
    """Simple keyword-based intent classification."""
    msg = message.lower()

    if "add task" in msg or "remember" in msg or "todo" in msg or "new task" in msg:
        return "add_task"
    if "complete" in msg or "done" in msg or "finish" in msg or "mark as complete" in msg:
        return "complete_task"
    if "list" in msg or "show tasks" in msg or "what are my tasks" in msg:
        return "list_tasks"

    return "chat"


# ------------------------
# Main Gemini Agent
# ------------------------
def ai_agent(user_input):
    """
    Main function for the Agent.
    1. Classifies user intent.
    2. Executes the corresponding tool (if applicable).
    3. Sends tool output and user input to Gemini for a natural response.
    """

    intent = classify_intent(user_input)
    tool_output = None
    
    print(f"-> Detected Intent: {intent}") # Debugging output

    # Route tasks to correct function
    if intent == "add_task":
        # Simple extraction of the task description after keywords
        task_desc = user_input.replace("add task", "").replace("remember", "").replace("todo", "").strip()
        tool_output = add_task(task_desc)

    elif intent == "complete_task":
        # Extract the first number found in the string as the task ID
        nums = [int(s) for s in user_input.split() if s.isdigit()]
        if nums:
            tool_output = complete_task(nums[0])
        else:
            tool_output = "Which task number would you like to mark as complete?"

    elif intent == "list_tasks":
        tool_output = list_tasks()

    # --- Prompt for Gemini ---
    prompt = f"""
You are a helpful and friendly productivity assistant named Nova.
Your goal is to summarize the outcome of a user's action or simply chat with the user.

Intent: {intent}
Tool Output: ---
{tool_output}
---

If Tool Output is present, acknowledge the task change (e.g., "I've added that task for you") or list the tasks clearly.
If the Intent is 'chat', simply respond to the User.
User: {user_input}
"""
    print("-> Calling Gemini...") # Debugging output
    
    # Call Gemini to generate the final, natural response
    gemini_response = call_gemini(prompt)

    # Check for API errors
    if gemini_response.startswith("❌"):
        return f"Agent encountered an internal error: {gemini_response}"

    return gemini_response


# ------------------------
# Example Usage
# ------------------------
if __name__ == "__main__":
    
    print("\n--- Productivity Agent Initialized (using gemini-2.5-flash) ---\n")

    # 1. Add Task
    response1 = ai_agent("add task to buy groceries after work")
    print(f"User: add task to buy groceries after work\nNova: {response1}\n")

    # 2. Add another Task
    response2 = ai_agent("remember to call the plumber tomorrow morning")
    print(f"User: remember to call the plumber tomorrow morning\nNova: {response2}\n")
    
    # 3. List Tasks
    response3 = ai_agent("show my tasks")
    print(f"User: show my tasks\nNova: {response3}\n")
    
    # 4. Complete Task (assuming ID 1)
    response4 = ai_agent("complete task 1")
    print(f"User: complete task 1\nNova: {response4}\n")

    # 5. Chat Intent
    response5 = ai_agent("What is the capital of France?")
    print(f"User: What is the capital of France?\nNova: {response5}\n")
