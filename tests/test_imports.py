import pytest

def test_core_imports():
    from core.orchestrator import main_workflow
    from core.logger import console, log_success
    assert callable(main_workflow)
    assert callable(log_success)

def test_agents_registry():
    from agents.registry import AGENTS
    assert isinstance(AGENTS, dict)
    assert "grok-fast" in AGENTS