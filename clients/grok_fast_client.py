# grok_fast_client.py — Grok Code Fast 1 with Auto-Help Request (v2.1)
# Implements the official Grok-Centric Collaboration Baseline (Nov 19, 2025)

import argparse
import json
import os
import sys
import textwrap
import uuid
import datetime
from pathlib import Path
import re
import requests

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.git_utils import git_commit_changes

def call_gemini_30_pro(messages: list[dict], temperature: float = 0.2) -> str:
    import google.generativeai as genai
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel("gemini-3.0-pro-latest")

    chat = model.start_chat()
    full_prompt = "\n\n".join([f"{m['role'].upper()}: {m['content']}" for m in messages])
    response = chat.send_message(
        full_prompt,
        generation_config=genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=32768,
            response_mime_type="text/plain"
        )
    )
    return response.text

# === CONFIGURATION ===
COLLAB_ROOT = Path(__file__).parent.parent.resolve()  # collaboration_archive or collaboration_framework
TASKS_DIR = COLLAB_ROOT / "tasks"
PROMPTS_DIR = COLLAB_ROOT / "prompts"

SYSTEM_PROMPT = textwrap.dedent("""\
    You are Grok Code Fast 1 — the primary programmatic coder in a Grok-centric collaboration system.

    CRITICAL RULES:
    • You may ONLY modify files in grok/ and shared/
    • Always output FULL file content in the exact format shown below
    • If you are unsure, stuck, or the problem requires high-level design/architecture → YOU MUST ASK FOR HELP

    WHEN TO ASK FOR HELP (mandatory):
    - Choosing between multiple valid algorithms/architectures
    - Bit-level optimizations, quantization tricks, or low-level tensor layouts
    - Designing new data structures or public APIs
    - Any task involving >3 non-trivial implementation choices
    - You estimate >70% chance of needing rework without guidance

    HOW TO ASK FOR HELP:
    Output exactly this block (and nothing else if you're only requesting help):
    ```request_help
    Question for Grok 4.1: [Your clear, concise question]
    Context files: shared/data_utils.py grok/quantizer.py
    ```

    REQUIRED OUTPUT FORMAT when implementing:
    ```python:shared/main.py
    # full new content
    ```

    Begin work now.
""").strip()

# === ARGUMENTS ===
parser = argparse.ArgumentParser()
parser.add_argument("--description", required=True)
parser.add_argument("--files", nargs="+", required=True)
parser.add_argument("--task-id", required=True, help="Original task ID (e.g. task_010)")
args = parser.parse_args()

CURRENT_TASK_ID = args.task_id
TASK_DESCRIPTION = args.description
TARGET_FILES = [Path(p) for p in args.files]

# === PROTOCOL SAFETY ===
for p in TARGET_FILES:
    try:
        rel = p.relative_to(COLLAB_ROOT)
        if rel.parts[0] not in {"grok", "shared", "docs", ".github", "pyproject.toml", "requirements.txt", "README.md", "LICENSE", "core", "agents", "clients"}:
            print(f"PROTOCOL VIOLATION: Cannot write to {p}", file=sys.stderr)
            sys.exit(1)
    except ValueError:
        print(f"PROTOCOL VIOLATION: Path {p} outside collaboration root", file=sys.stderr)
        sys.exit(1)

# === COLLECT CURRENT FILE CONTENTS ===
file_contexts = []
for full_path in TARGET_FILES:
    rel_path = full_path.relative_to(COLLAB_ROOT)
    if full_path.exists():
        content = full_path.read_text(encoding="utf-8")
        lang = rel_path.suffix.lstrip(".") or "text"
        file_contexts.append(f"### {rel_path}\n```{lang}\n{content.rstrip()}\n```")
    else:
        file_contexts.append(f"### {rel_path}  (NEW FILE)\n```text\n# File does not exist yet\n```")

user_message = f"""TASK ID: {CURRENT_TASK_ID}
TASK: {TASK_DESCRIPTION}

CURRENT FILES:
{"".join(file_contexts)}
"""

# === CALL GROK CODE FAST 1 ===
payload = {
    "messages": [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message}
    ],
    "temperature": 0.15,
    "max_tokens": 32768
}

try:
    resp = requests.post(
        os.getenv("OPENCODE_GROK_URL", "http://127.0.0.1:4242/v1/chat/completions"),
        json=payload,
        timeout=400
    )
    resp.raise_for_status()
    grok_output = resp.json()["choices"][0]["message"]["content"]
except Exception as e:
    print(f"Grok API error: {e}", file=sys.stderr)
    sys.exit(1)

# === DETECT HELP REQUEST OR AUTO-GEMINI ===
if "gemini" in TASK_DESCRIPTION.lower() or "ui" in TASK_DESCRIPTION.lower() or "frontend" in TASK_DESCRIPTION.lower():
    # Auto-consult Gemini 3.0 Pro instead of blocking
    gemini_messages = [
        {"role": "system", "content": "You are Gemini 3.0 Pro, expert in UX, frontend, API design, and Pydantic schemas."},
        {"role": "user", "content": user_message}
    ]
    gemini_response = call_gemini_30_pro(gemini_messages)

    # Save as proposal
    proposal_path = COLLAB_ROOT / "shared" / "proposals" / f"gemini_auto_{CURRENT_TASK_ID}.py"
    proposal_path.parent.mkdir(parents=True, exist_ok=True)
    proposal_path.write_text(f"# Gemini 3.0 Pro auto-proposal for {CURRENT_TASK_ID}\n\n{gemini_response}")
    print(f"Auto-consulted Gemini 3.0 Pro → proposal saved to {proposal_path}")
    sys.exit(0)  # Let next orchestrator cycle merge

help_request = re.search(r"```request_help\s*(.*?)\n(.*?)\n```", grok_output, re.DOTALL)
if help_request:
    question = help_request.group(1).strip().split("\n")[0]
    context_line = help_request.group(2).strip()
    context_files = re.findall(r'\S+', context_line.replace("Context files:", ""))

    # Create new task for Grok 4.1
    new_task_id = f"task_{int(CURRENT_TASK_ID.split('_')[1]) + 1:03d}"
    new_task = {
        "task_id": new_task_id,
        "description": f"[HELP REQUEST from {CURRENT_TASK_ID}] {question}\n\nOriginal task: {TASK_DESCRIPTION}\n\nRelevant files: {', '.join(context_files)}",
        "assignee": "grok-4.1",
        "files": [str(Path(f).relative_to(COLLAB_ROOT)) for f in context_files if Path(f).exists()],
        "status": "pending",
        "created_at": datetime.datetime.now(datetime.UTC).isoformat(),
        "depends_on": CURRENT_TASK_ID
    }

    task_file = TASKS_DIR / f"{new_task_id}.json"
    task_file.write_text(json.dumps(new_task, indent=2))
    print(f"\nGrok Code Fast 1 requested help → created {new_task_id}.json")
    print(f"Question: {question}")

    # Update original task to blocked
    orig_task_file = TASKS_DIR / f"{CURRENT_TASK_ID}.json"
    if orig_task_file.exists():
        orig = json.loads(orig_task_file.read_text())
        orig["status"] = "blocked"
        orig["blocked_by"] = new_task_id
        orig_task_file.write_text(json.dumps(orig, indent=2))

    # Generate clean prompt for user
    prompt_path = PROMPTS_DIR / f"grok41_prompt_{new_task_id}.txt"
    prompt_path.write_text(f"""Grok 4.1 Consultant Request ({new_task_id})

Original task blocked: {CURRENT_TASK_ID}
Question from Grok Code Fast 1:

{question}

Relevant context files attached (or below):
{', '.join(new_task['files'])}

Please provide architectural guidance, algorithm selection, or design decision.
""")
    print(f"Ready for Grok 4.1 → prompt saved to {prompt_path}")
    sys.exit(0)

# === NORMAL IMPLEMENTATION PATH ===
code_blocks = re.findall(r"```(?:\w+:)?([^\n`]+)\n(.*?)\n```", grok_output, re.DOTALL)
if not code_blocks:
    print("No valid code blocks found. Raw output:")
    print(grok_output)
    sys.exit(1)

written = []
for rel_str, code in code_blocks:
    rel_str = rel_str.strip()
    if ":" in rel_str:
        rel_str = rel_str.split(":", 1)[1]
    target = (COLLAB_ROOT / rel_str).resolve()

    # Final safety
    try:
        target.relative_to(COLLAB_ROOT)
    except ValueError:
        print(f"SAFETY BLOCK: Attempted write outside root: {target}")
        continue

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(code.rstrip() + "\n", encoding="utf-8")
    written.append(str(target.relative_to(COLLAB_ROOT)))

def generate_gemini_prompt(task_id: str, goal: str):
    context = []
    for path in Path(COLLAB_ROOT).rglob("*.py"):
        if "gemini/" in str(path) or "shared/" in str(path):
            rel = path.relative_to(COLLAB_ROOT)
            try:
                content = path.read_text(encoding="utf-8")
                context.append(f"File: {rel}\n```python\n{content}\n```")
            except:
                pass

    prompt = f"""You are Gemini 3.0 Pro. Task: {goal}
Relevant files attached.
Please output ONLY submittable code proposals using this format:
```python:shared/proposals/gemini_{task_id}.py
# your full code here
```
"""

    prompt_path = PROMPTS_DIR / f"gemini_{task_id}.md"
    prompt_path.write_text(prompt + "\n\n" + "\n\n".join(context))
    print(f"Gemini prompt ready: {prompt_path}")

print("Task completed successfully by Grok Code Fast 1")
print("Files updated:", ", ".join(written))

# Commit changes
git_commit_changes(f"Task {CURRENT_TASK_ID}: {TASK_DESCRIPTION[:60]}", author="grok-fast")