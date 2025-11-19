# logger.py
from rich.console import Console
from rich.table import Table
from rich import box
from datetime import datetime

console = Console()

def log_task_start(task):
    table = Table(title=f"Task {task['task_id']}", box=box.ROUNDED)
    table.add_column("Field")
    table.add_column("Value")
    table.add_row("Assignee", f"[bold cyan]{task['assignee']}[/]")
    table.add_row("Description", task['description'][:100] + "...")
    table.add_row("Files", "\n".join(task['files']))
    console.print(table)

def log_success(task_id, duration):
    console.print(f"[bold green]✓ Task {task_id} completed in {duration:.2f}s[/]")

def log_error(msg):
    console.print(f"[bold red]✗ {msg}[/]")

def log_retry(task_id, attempt):
    console.print(f"[yellow]Retrying {task_id} (attempt {attempt})[/]")