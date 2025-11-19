# Architecture (v1.0)

```
tasks/ → orchestrator → agents/registry → client → Git → CI → auto-merge → repeat
          ↑              ↓
      proposals       sandbox
```

Key invariants:
- No agent ever writes outside allowed directories
- Every change is a Git commit with proper author
- Tests must pass before merge
- All state lives in Git (no hidden DB)