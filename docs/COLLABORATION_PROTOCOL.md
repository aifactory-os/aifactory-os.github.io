# Collaboration Protocol v3.0

## Overview
AI Factory OS enables multiple AI agents to collaborate on software development tasks using strict protocols, atomic Git commits, and zero manual copy-paste.

## Agents
- **grok-fast**: Local programmatic coder for backend, quantization, training loops
- **gemini**: Web UI agent for UX, API design, documentation
- **grok-4.1**: Web UI agent for architectural review and design decisions

## Directory Ownership
- `grok/`: Owned by grok-fast
- `gemini/`: Owned by gemini
- `shared/`: Collaborative, except `shared/proposals/` for proposals
- `docs/`: Any agent

## Task Workflow
1. Tasks defined as JSON in `tasks/`
2. Orchestrator assigns to agents
3. Agents execute or handoff to web UI
4. Changes committed atomically
5. Proposals merged via review

## Protocol Enforcement
All file modifications must respect ownership rules. Violations are blocked.