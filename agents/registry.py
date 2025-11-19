# agents/registry.py
from pathlib import Path
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
    },
    "agent-4": {"executor": None, "handoff": None},
    "agent-5": {"executor": None, "handoff": None},
    "agent-6": {"executor": None, "handoff": None},
    "agent-7": {"executor": None, "handoff": None},
    "agent-8": {"executor": None, "handoff": None},
    "agent-9": {"executor": None, "handoff": None},
    "agent-10": {"executor": None, "handoff": None}
}

def register_agent(name, executor=None, handoff=None):
    """Register a new agent"""
    AGENTS[name] = {"executor": executor, "handoff": handoff}

def load_plugins():
    """Load agent plugins from agents/plugins/ directory"""
    import importlib.util
    plugins_dir = Path(__file__).parent / "plugins"
    if not plugins_dir.exists():
        return
    for plugin_file in plugins_dir.glob("*.py"):
        spec = importlib.util.spec_from_file_location(plugin_file.stem, plugin_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        # Assume plugin defines register() function
        if hasattr(module, 'register'):
            module.register(register_agent)

def dispatch_task(task):
    agent = AGENTS.get(task["assignee"])
    if agent["executor"]:
        return agent["executor"](task)
    elif agent["handoff"]:
        return agent["handoff"](task)
    else:
        raise ValueError(f"No handler for {task['assignee']}")