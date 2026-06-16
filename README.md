# polyglot-eval

A repo-agnostic AI agent that runs six Intermediate engineering eval tasks (I1–I6)
on any target repository using the **Claude Agent SDK**.

## Quick Start

```bash
# 1. Install
pip install -e .

# 2. Set API key
export ANTHROPIC_API_KEY=sk-ant-...

# 3. Run a single task (read-only, safe)
polyglot-eval --repo /path/to/some-repo --tasks I1

# 4. Run multiple tasks
polyglot-eval --repo . --tasks I1,I2

# 5. Run all tasks
polyglot-eval --repo . --tasks all

# 6. List available tasks
polyglot-eval --list-tasks
```

## Available Tasks

| ID | Title | Mode | Description |
|----|-------|------|-------------|
| **I1** | ER Diagram | read-only | Scan ORM models → Mermaid `erDiagram` + React UI viewer at localhost:5173 |
| **I2** | Flow Trace | read-only | Trace primary request path → Mermaid `sequenceDiagram` + React UI viewer at localhost:5174 |
| **I3** | Safe Change | writes repo (gated) | Minimal change on a branch, tests required, never commits |
| **I4** | Polyglot Pair | creates artifacts | FastAPI + Node.js currency service + CLI + tests from scratch |
| **I5** | Dockerize | creates artifacts | Dockerfile, build proof, run proof, health check |
| **I6** | Bug Diagnosis | writes repo (gated) | Reproduce → root cause → minimal fix → verify |

## CLI Reference

```
polyglot-eval [OPTIONS]

Options:
  --repo PATH         Target repository path (default: current directory)
  --tasks TASKS       Comma-separated task IDs: I1,I2,I3 or 'all' (default: all)
  --out PATH          Output directory for reports (default: <repo>/reports/)
  --autonomy MODE     gated | auto | dryrun (default: gated)
  --model MODEL       Model for all tasks (default: claude-opus-4-8)
  --list-tasks        Show all tasks and exit
```

### Autonomy Modes

| Mode | Behaviour |
|------|-----------|
| `gated` | **Default.** Prompts the operator before every file write or shell command. |
| `auto` | Writes without prompting. Hard-denies `git push`, `git commit`, `rm -rf`, `docker push`. |
| `dryrun` | No writes to the repo. Agent emits intended changes as diffs in the report. |

## Examples

```bash
# Generate ER diagram for a Django project
polyglot-eval --repo ~/projects/myapp --tasks I1

# Trace the checkout flow in an e-commerce repo
polyglot-eval --repo ~/projects/shop --tasks I2

# Make a specific change (gated — will prompt before each write)
polyglot-eval --repo . --tasks I3

# Build the polyglot pair in the current directory
polyglot-eval --repo . --tasks I4

# Run I1 + I2 concurrently (read-only tasks run in parallel)
polyglot-eval --repo . --tasks I1,I2

# Dry-run a bug fix (no repo changes, just the diagnosis report)
polyglot-eval --repo . --tasks I6 --autonomy dryrun
```

## Using Subagents in Another Repo (No Install Required)

Copy the content of [`UNIVERSAL_PROMPT.md`](./UNIVERSAL_PROMPT.md) and paste it into
Claude Code (or any Claude interface) while inside the target repository.

Claude will:
1. Show the subagent menu
2. Ask which task(s) you want to run + any task-specific inputs
3. Run **only** the selected subagent(s)
4. For I1/I2, automatically copy the prebuilt React UI from the central installation, drop in the analyzed `data.js`, and start the local dev server at localhost:5173/5174.
5. Write reports to `reports/` in the current directory

## Output

All reports are written to `<repo>/reports/` (or `--out` directory):

```
reports/
  SUMMARY.md                  # Pass/fail table for all tasks run
  I1_er_diagram.md            # I1 output
  I2_flow_trace.md            # I2 output
  I3_safe_change.md           # I3 output
  I4_polyglot_pair.md         # I4 output
  I5_dockerize.md             # I5 output
  I6_bug_diagnosis.md         # I6 output
  artifacts/
    I3/diff.patch             # I3 git diff
    I4/service/main.py        # I4 FastAPI service
    I4/service/test_service.py
    I4/client/index.js        # I4 Node CLI
    I4/README.md
    I5/Dockerfile             # I5 Docker artifacts
    I6/fix.patch              # I6 git diff
```

## Interactive Subagents (Claude Code)

The `.claude/agents/` directory contains subagent definitions that Claude Code
discovers automatically. Open any repo in Claude Code and ask:

```
/agent I1 — ER Diagram
```

or use the subagent picker in the Claude Code UI.

## Optional Dependencies

| Dependency | Purpose | Install |
|-----------|---------|---------|
| `@mermaid-js/mermaid-cli` | Full Mermaid render-validation (I1/I2) | `npm i -g @mermaid-js/mermaid-cli` |
| `docker` | Required for I5 | Platform installer |
| `node` / `npm` | Required for I4 Node client | https://nodejs.org |

## Auth

Set `ANTHROPIC_API_KEY` in your environment, or authenticate via:

```bash
ant auth login
```

## Safety Guarantees

polyglot-eval **never**:
- Commits to git
- Pushes to any remote
- Runs `rm -rf` or other destructive shell commands
- Pushes to Docker Hub or any registry
- Makes external network calls (except to Anthropic's API)

Write tasks always work on a dedicated branch (`polyglot-eval/<task-id>`) and leave the
main/master branch untouched.
