# Proof of execution — fixture-repo

Committed outputs from polyglot-eval against **`examples/fixture-repo`**.

## Contents

| Path | Description |
|------|-------------|
| `reports/SUMMARY.md` | Run summary |
| `reports/EXECUTION_LOG.md` | Command output (pytest, I4 tests) |
| `reports/I1_er_diagram.md` … `I6_bug_diagnosis.md` | Markdown reports |
| `reports/artifacts/I1–I6/data.json` | Dashboard payloads |
| `reports/artifacts/I3/diff.patch` | I3 safe-change diff |
| `reports/artifacts/I6/fix.patch` | I6 bug fix diff |
| `reports/artifacts/I4/service/` | FastAPI + pytest (4 tests) |
| `reports/artifacts/I4/client/` | Node CLI + test script |

## Regenerate

```bash
polyglot-eval generate-data --repo examples/fixture-repo
python -m polyglot_eval.build_proof_reports
cp examples/fixture-repo/reports/artifacts/I*/data.json examples/proof-of-execution/reports/artifacts/I*/ 
pytest
```

## Verify I4

```bash
cd reports/artifacts/I4/service && pytest -q
```
