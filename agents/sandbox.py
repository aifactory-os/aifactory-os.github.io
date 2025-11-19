import subprocess
import os

def run_in_sandbox(cmd: list[str]):
    return subprocess.run([
        "docker", "run", "--rm",
        "-v", f"{os.getcwd()}:/code",
        "-w", "/code",
        "--cap-drop=ALL",
        "python:3.12-slim",
        *cmd
    ], check=True)