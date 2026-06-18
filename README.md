# polyglot-eval

A **repo-agnostic AI agent** that runs six Intermediate engineering eval tasks (I1–I6) on any target repository using the **Claude Agent SDK**. Results are written as markdown reports and served in interactive React dashboards.

---

## Live dashboard & viewers

Open the hosted eval UI in your browser — no local setup required:

| # | Viewer | URL |
|---|--------|-----|
| 1 | **Combined dashboard** — all tasks I1–I6, stats, and drill-down panels | **https://polyglot-eval.vercel.app** |
| 2 | **I1 — ER Diagram** — entity map and Mermaid diagram | **https://polyglot-eval-i1.vercel.app** |
| 3 | **I2 — Flow Trace** — sequence diagram and step timeline | **https://polyglot-eval-i2.vercel.app** |

> **Quick link:** [polyglot-eval.vercel.app](https://polyglot-eval.vercel.app) — start here for the full overview and task results.

To publish fresh results after running eval on a repo:

```bash
export VERCEL_TOKEN=your_token
polyglot-eval deploy-ui --repo /path/to/your-repo
```

---

## About this repository

| | |
|---|---|
| **Purpose** | Evaluate how well an AI agent understands, changes, and ships code in an unfamiliar codebase |
| **Stack** | Python 3.10+ CLI · Claude Agent SDK · React + Vite viewers |
| **Target** | Any git repo — Django, React, Node, polyglot monorepos, etc. |
| **Safety** | Never commits, pushes, or runs destructive shell commands |

### What it does

1. **Scans or modifies** a target repo according to the selected task(s)
2. **Writes reports** to `<target-repo>/reports/` (markdown + JSON artifacts)
3. **Serves dashboards** at local ports so you can explore ER diagrams, flow traces, diffs, Docker proofs, and more

### Eval tasks (I1–I6)

| ID | Title | Mode | Local | Live |
|----|-------|------|-------|------|
| **I1** | ER Diagram | read-only | localhost:5173 | [polyglot-eval-i1.vercel.app](https://polyglot-eval-i1.vercel.app) |
| **I2** | Flow Trace | read-only | localhost:5174 | [polyglot-eval-i2.vercel.app](https://polyglot-eval-i2.vercel.app) |
| **I3** | Safe Change | writes repo (gated) | Dashboard | Dashboard |
| **I4** | Polyglot Pair | creates artifacts | Dashboard | Dashboard |
| **I5** | Dockerize | creates artifacts | Dashboard | Dashboard |
| **I6** | Bug Diagnosis | writes repo (gated) | Dashboard | Dashboard |
| **ALL** | Combined dashboard | read-only | localhost:5175 | [polyglot-eval.vercel.app](https://polyglot-eval.vercel.app) |

---

## Prerequisites

| Tool | Version | Required for |
|------|---------|--------------|
| Python | 3.10+ | CLI and orchestrator |
| Node.js + npm | 18+ | React dashboards (I1, I2, combined) |
| `ANTHROPIC_API_KEY` | — | AI task execution |
| Docker | latest | I5 only |
| `@mermaid-js/mermaid-cli` | optional | Full Mermaid render validation (I1/I2) |

---

## Local setup

### 1. Clone and install

```bash
git clone https://github.com/Shivendra-11/PolyGlot-eval.git
cd PolyGlot-eval

# Create a virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install polyglot-eval in editable mode
pip install -e .

# Optional: Claude Agent SDK for full agent runs
pip install -e ".[sdk]"

# Optional: dev tools (pytest, httpx)
pip install -e ".[dev]"
```

### 2. Authenticate

```bash
# Option A — environment variable
export ANTHROPIC_API_KEY=sk-ant-...

# Option B — Claude CLI login
ant auth login
```

### 3. Install dashboard UI dependencies (first run only)

```bash
cd polyglot_eval/ui/dashboard && npm install && cd ../../..
cd polyglot_eval/ui/i1 && npm install && cd ../../..
cd polyglot_eval/ui/i2 && npm install && cd ../../..
```

Or let the CLI install them automatically on first `serve-ui`.

### 4. Run against a target repo

```bash
# Read-only ER diagram
polyglot-eval --repo /path/to/your-repo --tasks I1

# Multiple tasks
polyglot-eval --repo . --tasks I1,I2

# All tasks
polyglot-eval --repo . --tasks all

# Dry-run (no writes)
polyglot-eval --repo . --tasks I3 --autonomy dryrun
```

### 5. View results in the browser

```bash
# Combined dashboard (aggregates I1–I6 from reports/)
polyglot-eval serve-ui --task dashboard --repo /path/to/your-repo

# Individual viewers
polyglot-eval serve-ui --task I1 --data /path/to/your-repo/reports/artifacts/I1/data.json
polyglot-eval serve-ui --task I2 --data /path/to/your-repo/reports/artifacts/I2/data.json

# Generate sample dashboard data + launch (no AI run required)
polyglot-eval generate-data --repo /path/to/your-repo --serve

# Deploy to Vercel (unique URLs per repo)
export VERCEL_TOKEN=your_token
polyglot-eval deploy-ui --repo /path/to/your-repo
```

Open **http://localhost:5175** for the combined dashboard locally, or use the [live dashboard](https://polyglot-eval.vercel.app).

---

## CLI reference

```
polyglot-eval [OPTIONS]

Options:
  --repo PATH         Target repository path (default: current directory)
  --tasks TASKS       Comma-separated: I1,I2,I3 or 'all' (default: all)
  --out PATH          Output directory (default: <repo>/reports/)
  --autonomy MODE     gated | auto | dryrun (default: gated)
  --model MODEL       Model for all tasks (default: claude-opus-4-8)
  --list-tasks        Show all tasks and exit

Subcommands:
  serve-ui            Launch React viewers (I1, I2, dashboard, all)
  generate-data       Build dashboard JSON from repo scan (no AI)
  deploy-ui           Deploy dashboard + I1 + I2 to Vercel (fixed URLs)
```

### Autonomy modes

| Mode | Behaviour |
|------|-----------|
| `gated` | **Default.** Prompts before every file write or shell command. |
| `auto` | Writes without prompting. Hard-denies `git push`, `git commit`, `rm -rf`, `docker push`. |
| `dryrun` | No repo writes. Agent emits intended changes as diffs in the report. |

---

## Project structure

```
PolyGlot-eval/
├── polyglot_eval/
│   ├── cli.py                 # Entry point
│   ├── orchestrator.py        # Task runner
│   ├── dashboard_builder.py   # Aggregates I1–I6 into dashboard data
│   ├── generate_all_data.py   # Offline data generator (repo-agnostic)
│   ├── repo_scanner.py        # Static scan: entities, routes, entry points
│   ├── vercel_deploy.py       # Vercel deploy (polyglot-eval*.vercel.app)
│   ├── ui_launcher.py         # Vite dev server launcher
│   ├── tasks/                 # I1–I6 task definitions
│   └── ui/
│       ├── dashboard/         # Combined dashboard (port 5175)
│       ├── i1/                # ER diagram viewer (port 5173)
│       └── i2/                # Flow trace viewer (port 5174)
├── .claude/agents/            # Claude Code subagent definitions
├── UNIVERSAL_PROMPT.md        # Paste into any repo without installing
├── pyproject.toml
└── README.md                  # This file (GitHub only — not shown in the live UI)
```

---

## Output layout

Reports are written to `<target-repo>/reports/`:

```
reports/
  SUMMARY.md
  polyglot-deploy.json    # Live Vercel URLs (after deploy-ui)
  I1_er_diagram.md
  I2_flow_trace.md
  I3_safe_change.md
  I4_polyglot_pair.md
  I5_dockerize.md
  I6_bug_diagnosis.md
  artifacts/
    I1/data.json
    I2/data.json
    I3/diff.patch
    I4/service/ ...
    I5/Dockerfile
    I6/fix.patch
```

### Proof of execution (bundled)

Sample outputs from a real run on the bundled **fixture-repo** (repo-agnostic Python app):

- [`examples/fixture-repo/`](examples/fixture-repo/) — minimal target repo with tests and Dockerfile
- [`examples/proof-of-execution/reports/`](examples/proof-of-execution/reports/) — committed artifacts:
  - `SUMMARY.md`, `EXECUTION_LOG.md`, `I1_er_diagram.md` … `I6_bug_diagnosis.md`
  - `artifacts/I3/diff.patch`, `artifacts/I6/fix.patch`
  - `artifacts/I4/service/` — FastAPI + **4 pytest tests**
  - `artifacts/I4/client/` — Node CLI

Regenerate:

```bash
polyglot-eval generate-data --repo examples/fixture-repo
python -m polyglot_eval.build_proof_reports
pytest   # includes integration tests against proof bundle
```

---

## Using in Cursor / Claude Code

### Slash command

```
/polyglot-eval
/polyglot-eval --repo /path/to/repo --tasks I1,I2
```

### Subagents

Open any repo in Claude Code and use the subagent picker, or:

```
/agent I1 — ER Diagram
```

Agent definitions live in `.claude/agents/`.

### Without installing

Copy [`UNIVERSAL_PROMPT.md`](./UNIVERSAL_PROMPT.md) into Claude while inside the target repository.

---

## Safety guarantees

polyglot-eval **never**:

- Commits to git
- Pushes to any remote
- Runs `rm -rf` or other destructive shell commands
- Pushes to Docker Hub or any registry

Write tasks use a dedicated branch (`polyglot-eval/<task-id>`) and leave `main`/`master` untouched.

---

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests (permissions, Mermaid validator, dashboard builder, repo scanner)
pytest

# Lint
ruff check . && ruff format .

# Offline repo-agnostic data generation (no AI)
polyglot-eval generate-data --repo examples/fixture-repo

# Rebuild dashboard after code changes
polyglot-eval serve-ui --task dashboard --repo examples/fixture-repo
```

### Test coverage

| Module | Tests |
|--------|-------|
| `polyglot_eval/permissions.py` | Hard-deny patterns, UI guard, safe bash, `validate_repo_state` |
| `polyglot_eval/tools/report_tools.py` | Mermaid structural lint, `submit_report`, `save_artifact` |
| `polyglot_eval/dashboard_builder.py` | Artifact loading, dashboard aggregation |
| `polyglot_eval/repo_scanner.py` | Repo-agnostic entity/flow scan on fixture-repo |
| `polyglot_eval/build_proof_reports.py` | Generate markdown reports from proof artifacts |
| I3 / I6 kickoffs | Self-contained default prompts (no runtime input required) |
| `tests/test_integration.py` | Proof bundle + I4 pytest + dashboard integration |

---

## License

MIT — see repository for details.
