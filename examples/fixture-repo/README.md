# Fixture repo

Minimal Python task store used as a **repo-agnostic** target for polyglot-eval demos and proof-of-execution artifacts.

```bash
pytest -q
```

Known edge case: `TaskStore.average_title_length()` raises on an empty store (intentional for I6 bug-diagnosis demos).
