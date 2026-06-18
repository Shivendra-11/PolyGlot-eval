# Fixture repo

Minimal Python task store used as a **repo-agnostic** target for polyglot-eval demos and proof-of-execution artifacts.

```bash
pytest -q
```

Known edge case (I6 demo): `TaskStore.average_title_length()` previously raised on empty store — fixed in proof bundle with regression test.
