# Contributing to AI Factory OS

1. All work happens via tasks in `/tasks/`
2. Never push directly to main — only via proposals → PR → auto-merge
3. To add a new agent → implement `AgentProtocol` and register in `agents/registry.py`
4. Run `python -m agents.auto_agent` locally to test