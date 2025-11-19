# agents/__init__.py
from .registry import AGENTS, dispatch_task
__all__ = ["AGENTS", "dispatch_task"]