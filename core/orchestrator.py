"""Orchestrator v4.0 with DAG, retries, rich logging."""

import json
import os
import subprocess
import sys
import time
import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.logger import log_task_start, log_success, log_error, log_retry
from agents.registry import AGENTS, dispatch_task

# --- Configuration ---
import pathlib
SCRIPT_DIR = pathlib.Path(__file__).parent
COLLABORATION_ROOT = SCRIPT_DIR.parent
TASKS_DIR = COLLABORATION_ROOT / 'tasks'
WORKSPACE_DIR = COLLABORATION_ROOT # Base for grok/gemini/shared (project files)
PROMPTS_DIR = COLLABORATION_ROOT / 'prompts'
PROTOCOL_DIRS = [
    'grok',
    'gemini',
    'shared',
    'docs' # Docs dir is also part of Grok's proposed structure
]

# --- 1. Environment and Task Management ---

def setup_environment():
    """Ensures the core directories for collaboration exist under COLLABORATION_ROOT."""
    print("Setting up environment...")
    
    # Create the main collaboration directories as per Grok's proposal
    # These are directly under COLLABORATION_ROOT
    for subdir in PROTOCOL_DIRS:
        path = COLLABORATION_ROOT / subdir
        path.mkdir(parents=True, exist_ok=True)
        print(f"  - Created/Ensured: {path}/")

    # Ensure TASKS_DIR is created
    TASKS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"  - Created/Ensured Tasks Dir: {TASKS_DIR}/")
    
    # Ensure PROMPTS_DIR is created
    PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"  - Created/Ensured Prompts Dir: {PROMPTS_DIR}/")

def load_task(task_id: str) -> dict:
    """Loads a single task by its task_id."""
    task_file_path = TASKS_DIR / f"{task_id}.json"
    try:
        with open(task_file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # This might happen if a task file is deleted or not yet created
        return None
    except json.JSONDecodeError:
        print(f"ERROR: Task file {task_file_path} contains invalid JSON.")
        sys.exit(1)

def save_task(task: dict):
    """Saves a single task to its JSON file."""
    task_file_path = TASKS_DIR / f"{task['task_id']}.json"
    with open(task_file_path, 'w') as f:
        json.dump(task, f, indent=2)

def load_all_tasks() -> list:
    """Loads all task files from the TASKS_DIR."""
    tasks = []
    if not TASKS_DIR.exists():
        TASKS_DIR.mkdir(parents=True) # Ensure TASKS_DIR exists
        return []
        
    for filename in TASKS_DIR.iterdir():
        if filename.suffix == ".json":
            task_id = filename.stem
            task = load_task(task_id)
            if task:
                tasks.append(task)
    # Sort tasks by task_id to ensure consistent processing order
    return sorted(tasks, key=lambda t: t['task_id'])


def get_next_task(tasks: list) -> dict:
    """Finds the next ready task with status 'pending', considering dependencies."""
    pending = [t for t in tasks if t['status'] == 'pending']
    ready = [t for t in pending if all(dep['status'] == 'completed'
            for dep_id in t.get('depends_on', [])
            for dep in tasks if dep['task_id'] == dep_id)]
    return min(ready, key=lambda t: t.get('priority', 10), default=None)

def update_task_status(task: dict, new_status: str):
    """Updates the status of a specific task, updates timestamp, and saves it."""
    task['status'] = new_status
    task['updated_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    save_task(task)


# --- 2. Protocol Enforcement ---

def merge_proposals():
    """Merges proposals from shared/proposals/ into shared/app/main.py."""
    proposals_dir = COLLABORATION_ROOT / 'shared' / 'proposals'
    if not proposals_dir.exists():
        proposals_dir.mkdir(parents=True)
    proposals = [f for f in proposals_dir.iterdir() if f.suffix in ['.py', '.json']]
    if not proposals:
        return
    # Simple merge: append all proposals with headers
    merged_code = ""
    for prop in sorted(proposals):
        content = prop.read_text(encoding='utf-8')
        header = f"# >>>>>>> PROPOSAL {prop.name}\n"
        footer = f"# <<<<<<< END {prop.name}\n"
        merged_code += header + content + footer + "\n\n"

    main_path = COLLABORATION_ROOT / 'shared' / 'app' / 'main.py'
    original = main_path.read_text(encoding='utf-8') if main_path.exists() else ""
    new_content = original.rstrip() + "\n\n# === AUTO-MERGED PROPOSALS ===\n" + merged_code
    main_path.write_text(new_content, encoding='utf-8')
    # Clear proposals
    for prop in proposals:
        prop.unlink()
    print(f"  [MERGE] Merged {len(proposals)} proposals into shared/app/main.py")

def check_protocol(task):
    """Checks if the task assignee is allowed to modify the target files based on updated protocol."""
    assignee = task['assignee']
    files = task['files']

    for file_path in files:
        # File paths are now relative to COLLABORATION_ROOT (e.g., 'gemini/my_file.txt')
        # Extract the top-level directory from the file_path
        parts = file_path.split('/')
        top_dir = parts[0]

        if top_dir == 'gemini' and assignee != 'gemini':
            print(f"  [PROTOCOL VIOLATION] Task assigned to '{assignee}' attempts to modify file in 'gemini/' directory.")
            return False
        elif top_dir == 'grok' and assignee != 'grok-fast':
            print(f"  [PROTOCOL VIOLATION] Task assigned to '{assignee}' attempts to modify file in 'grok/' directory.")
            return False
        elif top_dir == 'shared':
            # Allow writing to shared/proposals/ for both agents
            if len(parts) > 1 and parts[1] == 'proposals':
                continue  # Allowed
            else:
                # Direct writes to shared/ are not allowed; use proposals
                print(f"  [PROTOCOL VIOLATION] Direct write to shared/ not allowed. Use shared/proposals/ for proposals.")
                return False
        elif top_dir == 'docs':
            continue  # Docs are allowed for any agent

    # If all checks pass
    return True

# --- 3. Agent Execution Functions ---

def handle_gemini_handoff(task):
    """
    Generates a prompt for Gemini and provides instructions to the user.
    Updates the task status to 'awaiting_gemini_input'.
    """
    print(f"  [HANDOFF] Task {task['task_id']} is assigned to Gemini. Manual intervention is required.")
    
    # 1. Generate the prompt content
    prompt_filename = f"gemini_prompt_{task['task_id']}.md"
    prompt_filepath = PROMPTS_DIR / prompt_filename
    
    # Read the content of the files to be edited for the prompt
    file_contents_for_prompt = ""
    for relative_path in task['files']:
        full_path = COLLABORATION_ROOT / relative_path
        try:
            content = full_path.read_text(encoding='utf-8')
            file_contents_for_prompt += f"--- START OF {relative_path} ---\n```{content}\n```\n--- END OF {relative_path} ---\n\n"
        except FileNotFoundError:
            file_contents_for_prompt += f"--- NOTE: File '{relative_path}' not found. Please create it. ---\n\n"

    # Construct the final prompt for the user/Gemini
    prompt_content = f"""
# Gemini Task Handoff: {task['task_id']}

**Description:** {task['description']}

## Instructions for Gemini Pro Web UI:
1. Review the task description and file contents below.
2. Perform the required code modifications.
3. In your response, provide the **complete, final content** of each modified file in a separate fenced code block. The code block should be marked with the language and the relative file path, like this:

   ````markdown
   ```python:path/to/your/file.py
   # ... complete new content of the file ...
   ```
   ````

## File Contents:
{file_contents_for_prompt}
"""
    
    prompt_filepath.write_text(prompt_content, encoding='utf-8')

    # 2. Update task status
    update_task_status(task, 'awaiting_gemini_input')
    
    # 3. Print instructions for the user
    print("\n" + "="*50)
    print("  ACTION REQUIRED: HANDOFF TO GEMINI")
    print("="*50)
    print(f"  1. A prompt has been generated at: {prompt_filepath}")
    print(f"  2. Please go to the Gemini web UI, use the content of this file as your prompt.")
    print("     It is highly recommended to **attach the files** instead of relying on the pasted content.")
    print("     Files to attach:")
    for file in task['files']:
        print(f"       - {COLLABORATION_ROOT / file}")
    print(f"  3. Once you have the response from Gemini, run the ingestion script.")
    print(f"     Example command: python process_gemini_response.py --task {task['task_id']}")
    print("="*50 + "\n")
    
    return False # Return False to indicate the orchestrator should stop

def handle_grok_4_1_handoff(task):
    """
    Generates a prompt for Grok 4.1 and provides instructions to the user.
    Updates the task status to 'awaiting_grok_4_1_input'.
    """
    print(f"  [HANDOFF] Task {task['task_id']} is assigned to Grok 4.1. Manual intervention is required.")
    
    # 1. Generate the prompt content
    prompt_filename = f"grok_4_1_prompt_{task['task_id']}.md"
    prompt_filepath = PROMPTS_DIR / prompt_filename
    
    # Read the content of the files to be edited/referenced for the prompt
    file_contents_for_prompt = ""
    if 'files' in task and task['files']:
        for relative_path in task['files']:
            full_path = COLLABORATION_ROOT / relative_path
            try:
                content = full_path.read_text(encoding='utf-8')
                file_contents_for_prompt += f"--- START OF {relative_path} ---\n```{content}\n```\n--- END OF {relative_path} ---\n\n"
            except FileNotFoundError:
                file_contents_for_prompt += f"--- NOTE: File '{relative_path}' not found. Please create it. ---\n\n"
    else:
        file_contents_for_prompt = "No specific files are referenced in this task. Grok 4.1 might be expected to generate new content."

    # Construct the final prompt for the user/Grok 4.1
    prompt_content = f"""
# Grok 4.1 Task Handoff: {task['task_id']}

**Description:** {task['description']}

## Instructions for Grok 4.1 Web UI:
1. Review the task description and any provided file contents below.
2. Perform the requested analysis, design, or code generation.
3. In your response, provide your output in the most appropriate and structured format (e.g., Markdown, fenced code blocks for code, Mermaid syntax for diagrams).
4. If you are modifying files or generating new ones, use the fenced code block format with relative paths, similar to Gemini's expected output:

   ````markdown
   ```python:path/to/your/file.py
   # ... complete new content of the file ...
   ```
   ````

## File Contents (for reference or modification):
{file_contents_for_prompt}
"""
    
    prompt_filepath.write_text(prompt_content, encoding='utf-8')

    # 2. Update task status
    update_task_status(task, 'awaiting_grok_4_1_input')
    
    # 3. Print instructions for the user
    print("\n" + "="*50)
    print("  ACTION REQUIRED: HANDOFF TO GROK 4.1")
    print("="*50)
    print(f"  1. A prompt has been generated at: {prompt_filepath}")
    print(f"  2. Please go to the Grok 4.1 web UI, use the content of this file as your prompt.")
    print("     It is highly recommended to **attach any relevant files** instead of relying on the pasted content.")
    if 'files' in task and task['files']:
        print("     Files to attach:")
        for file in task['files']:
            print(f"       - {COLLABORATION_ROOT / file}")
    print(f"  3. Once you have the response from Grok 4.1, run the ingestion script (to be created).")
    print(f"     Example command: python process_grok_4_1_response.py --task {task['task_id']}")
    print("="*50 + "\n")
    
    return False # Return False to indicate the orchestrator should stop

def execute_grok_fast_task(task):
    """Executes tasks assigned to 'grok-fast' by calling the client script."""
    print(f"  [Grok-Fast] Delegating task {task['task_id']} to client script...")
    
    # Construct full paths for the client script
    full_file_paths = [str(COLLABORATION_ROOT / fp) for fp in task['files']]
    
    # Ensure directories exist for Grok's target files
    for full_path in full_file_paths:
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        # For new files, create them empty first so grok_fast_client can read/modify
        if not os.path.exists(full_path):
            with open(full_path, 'w') as f: f.write(f"# Initial file for task {task['task_id']} by Orchestrator\n")

    command = [
        sys.executable,
        str(SCRIPT_DIR.parent / 'clients' / 'grok_fast_client.py'),
        '--description', task['description'],
        '--task-id', task['task_id']
    ]

    # Only add the --files argument if the list of files is not empty
    if full_file_paths:
        command.extend(['--files'] + full_file_paths)
    
    print(f"  [DEBUG] Running command: {' '.join(command)}") # Added for debugging

    try:
        # We don't capture output so the client can print directly to the console for debugging
        result = subprocess.run(command, text=True, check=True, encoding='utf-8')
        print(f"  [Grok-Fast] Task {task['task_id']} complete.")
        return True
            
    except subprocess.CalledProcessError as e:
        print(f"  [Grok-Fast] ERROR: Client script failed for task {task['task_id']}.")
        print("  --- Grok-Fast Client STDERR ---\n" + e.stderr.strip() + "\n  ---------------------------------")
        return False
    except FileNotFoundError:
        print(f"  [Grok-Fast] ERROR: 'grok_fast_client.py' not found at {SCRIPT_DIR.parent / 'clients' / 'grok_fast_client.py'}.")
        return False

# Set up agent registry
AGENTS["grok-fast"]["executor"] = execute_grok_fast_task
AGENTS["gemini"]["handoff"] = handle_gemini_handoff
AGENTS["grok-4.1"]["handoff"] = handle_grok_4_1_handoff

# --- 4. Main Workflow ---

def main_workflow():
    """The main execution loop of the orchestrator."""
    print("====================================================")
    print("  Multi-Agent Orchestrator (Protocol Version 4.0)  ")
    print("====================================================")

    setup_environment()
    merge_proposals()  # Merge any pending proposals
    tasks = load_all_tasks()

    while True:
        current_task = get_next_task(tasks)

        if not current_task:
            print("\nAll tasks completed. Exiting.")
            break

        log_task_start(current_task)

        # PROTOCOL ENFORCEMENT
        if not check_protocol(current_task):
            success = False
            new_status = 'failed'
            log_error("Task failed due to protocol violation. Stopping orchestrator.")
        else:
            # If protocol check passes, execute the task
            success = False
            start_time = time.time()

            try:
                success = dispatch_task(current_task)
            except ValueError as e:
                print(f"  ERROR: {e}")

            end_time = time.time()

            if success:
                new_status = 'completed'
                log_success(current_task['task_id'], end_time - start_time)
            else:
                # Retry logic
                if current_task.get("retry_count", 0) < 3:
                    current_task["retry_count"] = current_task.get("retry_count", 0) + 1
                    new_status = 'pending'  # retry next loop
                    log_retry(current_task['task_id'], current_task['retry_count'])
                    success = True  # Don't break the loop
                else:
                    new_status = 'failed'
                    log_error(f"Task {current_task['task_id']} failed after retries. Stopping orchestrator.")

        # Update and save the specific task file
        update_task_status(current_task, new_status)

        if not success:
            break # Stop the loop if a task fails

        # Re-load all tasks to reflect changes (e.g., status update) and get new tasks if any were added
        # This is important if task dependencies or new tasks are created during execution
        tasks = load_all_tasks()
            
    print("\n========================================\n  Orchestrator run finished.\n========================================")

if __name__ == "__main__":
    main_workflow()