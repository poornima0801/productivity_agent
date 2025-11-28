import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Load Gemini API Key
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")

# Correct REST endpoint (2025)
API_URL = "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent"


# ------------------------
# Gemini Request Function
# ------------------------
def call_gemini(prompt):
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
    except Exception as e:
        return f"❌ Gemini API Error: {response.text}"

    # Extract model response
    return response.json()["candidates"][0]["content"]["parts"][0]["text"]


# ------------------------
# Simple JSON Task Storage
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
# Agent Tools
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

    if "add task" in msg or "remember" in msg or
