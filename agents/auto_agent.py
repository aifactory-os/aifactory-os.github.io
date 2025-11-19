# agents/auto_agent.py
import time
import subprocess

while True:
    result = subprocess.run(["python", "core/orchestrator.py"], capture_output=True, text=True)
    print(result.stdout)
    if "All tasks completed" in result.stdout:
        print("Idle — waiting for new tasks...")
        time.sleep(30)
    else:
        time.sleep(5)