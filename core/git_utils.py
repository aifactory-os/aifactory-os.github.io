# git_utils.py
import subprocess
from pathlib import Path

COLLAB_ROOT = Path(__file__).parent.parent

def git_commit_changes(message: str, author: str = "grok-fast"):
    """Commit all changes with proper author"""
    try:
        subprocess.run(["git", "add", "."], cwd=COLLAB_ROOT, check=True, capture_output=True)
        subprocess.run([
            "git", "commit", "-m", message,
            f"--author={author} <agent@{author}.local>"
        ], cwd=COLLAB_ROOT, check=True, capture_output=True)
        print(f"Committed: {message}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Git commit failed: {e.stderr.decode()}")
        return False