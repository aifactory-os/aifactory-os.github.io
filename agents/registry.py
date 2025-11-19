# agents/registry.py
AGENTS = {
    "grok-fast": {
        "executor": None,  # Will be set after import
        "handoff": None
    },
    "gemini": {
        "executor": None,
        "handoff": None  # Will be set after import
    },
    "grok-4.1": {
        "executor": None,
        "handoff": None  # Will be set after import
    }
}

def dispatch_task(task):
    agent = AGENTS.get(task["assignee"])
    if agent["executor"]:
        return agent["executor"](task)
    elif agent["handoff"]:
        return agent["handoff"](task)
    else:
        raise ValueError(f"No handler for {task['assignee']}")