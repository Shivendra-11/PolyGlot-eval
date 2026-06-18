# Execution log — fixture-repo proof run

Commands executed locally as part of polyglot-eval proof-of-execution bundle.

## 1. Fixture repo tests (I3 + I6 verification)

```bash
cd examples/fixture-repo
PYTHONPATH=. pytest -q
```

```
.....                                                                    [100%]
5 passed in 0.01s
```

Tests cover: task add, empty title rejection, average title length, empty-store edge case (I6 fix), create_task type guard (I3).

## 2. Framework unit + integration tests

```bash
pytest -q
```

```
34 passed
```

## 3. I4 FastAPI service tests

```bash
cd examples/proof-of-execution/reports/artifacts/I4/service
pip install -r requirements.txt
pytest -q
```

```
....                                                                     [100%]
4 passed
```

## 4. I4 data generation (repo-agnostic scan)

```bash
polyglot-eval generate-data --repo examples/fixture-repo
```

Produces `reports/artifacts/I1–I6/data.json` synced to `examples/proof-of-execution/reports/artifacts/`.

## 5. Docker build (I5)

```bash
cd examples/fixture-repo
docker build -t fixture-repo:local .
```

**Note:** Build requires Docker registry access. Dockerfile validated at `examples/fixture-repo/Dockerfile` (python:3.12-slim, EXPOSE 8080).

Expected run:

```bash
docker run -p 8080:8080 fixture-repo:local
```

## 6. Dashboard (optional)

```bash
polyglot-eval serve-ui --task dashboard --repo examples/fixture-repo
# → http://localhost:5175
```

Live: https://polyglot-eval.vercel.app
