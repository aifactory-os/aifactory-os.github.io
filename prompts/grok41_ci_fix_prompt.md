# Prompt for Grok 4.1: Fix CI Import Issues

Hello Grok 4.1,

I have a Python project with the following structure:

```
aifactory-os.github.io/
├── core/
│   ├── __init__.py
│   ├── orchestrator.py
│   └── logger.py
├── agents/
│   ├── __init__.py
│   └── registry.py
├── clients/
├── shared/
├── tests/
│   ├── test_api.py
│   └── test_imports.py
├── pyproject.toml
└── requirements.txt
```

The project is set up as a Python package with pyproject.toml, and all directories have __init__.py files.

In GitHub Actions CI, I'm running:
```bash
pip install -e .
PYTHONPATH=. pytest -vv
```

But the tests are still failing with:
```
ModuleNotFoundError: No module named 'core'
ModuleNotFoundError: No module named 'agents'
```

The tests contain:
```python
from core.orchestrator import main_workflow
from agents.registry import AGENTS
```

What could be causing this import failure in CI? The local development environment works fine, but CI fails.

Please provide a comprehensive solution to fix the import issues in GitHub Actions CI. Consider:

1. Python path configuration
2. Package installation issues
3. pytest configuration
4. CI environment differences
5. Any other potential causes

Provide the exact changes needed to pyproject.toml, the CI workflow, and any other files to make the imports work in CI.

Thank you!