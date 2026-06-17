"""I2 — Flow Trace + React Viewer UI

Read-only analysis task. Traces the primary request/event path and serves the pre-built
React viewer from the polyglot-eval install at localhost:5174.
The target repo receives only ``reports/artifacts/I2/data.js`` — no UI scaffold files.
"""

from .base import Deliverable, TaskSpec

_SYSTEM_PROMPT = """\
You are a senior software engineer performing a deep code trace. You will trace the most
important request/event flow (read-only), then produce a Mermaid sequenceDiagram and a
Markdown report.

## 🚫 DO NOT GENERATE FRONTEND CODE IN THE TARGET REPO
The React UI is **pre-built** in the polyglot-eval installation and served centrally.
You write **exactly one data file** in the target repo:
  `reports/artifacts/I2/data.json`  (preferred) or `data.js`
You must **NOT** create or copy App.jsx, package.json, vite.config.js, index.html, main.jsx,
App.css, or anything under `reports/artifacts/I2/ui/`.

After writing data.js, launch the viewer with **one command**:
```bash
polyglot-eval serve-ui --task I2 --data reports/artifacts/I2/data.json
```
That prints the localhost URL (http://localhost:5174). Do not run npm in the target repo.

## Phase 1 — Deep Trace (read-only)

Trace the **full** request path end-to-end (15–25 steps). Include all external I/O.

### Rules
1. **Read, never write in Phase 1.**
2. **Cite file + function for every step.**
3. **Flag uncertainty.** Dynamic dispatch, DI containers, runtime plugins → say so.
4. **Identify all external I/O.** DB queries, HTTP calls, queue messages, file writes, cache ops.
5. **Be selective.** Do NOT deep-dive into utility files, tests, or configs.

### Trace strategy
- Entry point: grep for `@app.get`, `@app.post`, `router.`, `addEventListener`, `main(`
- If the kickoff specifies an endpoint/function, trace that. Otherwise auto-detect.
- Follow the call chain file by file (max 10-15 files).
- Mark every external I/O interaction as a distinct step.

## Phase 2 — Write ONLY `reports/artifacts/I2/data.json`

Write valid JSON with keys: repoName, tracedFlow, generatedAt, status, mermaidDiagram,
entryPoint, steps, externalDeps, sideEffects, uncertainty.
ioType values: db_write, db_read, http_call, queue_publish, queue_consume, file_write, cache_set, null.
Use REAL data from Phase 1. This is the **only** file you create in the target repo.

## Phase 3 — Launch central UI (one Bash command)

```bash
polyglot-eval serve-ui --task I2 --data reports/artifacts/I2/data.json
```

Print the URL returned by the command.

## Phase 4 — Report

Call `mcp__report__submit_report` LAST, after the UI URL is confirmed.

## Deliverable contract
{contract}
"""

_KICKOFF = """\
Please trace the primary request/event flow through this repository.

Write ONLY `reports/artifacts/I2/data.json`, then run:
  polyglot-eval serve-ui --task I2 --data reports/artifacts/I2/data.json

Do NOT generate or copy any React/Vite files into the target repo.
Submit the report last.
"""

_DELIVERABLES = [
    Deliverable("entry_point", "The entry-point file, function/route, and how it is registered"),
    Deliverable(
        "steps",
        "Ordered list of every step: file path, function name, what it does, I/O type if applicable",
    ),
    Deliverable(
        "external_deps",
        "All external dependencies called (HTTP APIs, SDKs, queues) with file/line citations",
    ),
    Deliverable(
        "side_effects",
        "All side effects: DB writes, queue publishes, file writes, cache sets — each with citation",
    ),
    Deliverable(
        "sequence_diagram",
        "A valid Mermaid sequenceDiagram (also include the raw string in the `mermaid` list)",
    ),
    Deliverable(
        "uncertainty",
        "Any parts of the trace that are dynamic or could not be statically resolved, and why",
    ),
    Deliverable(
        "ui_instructions",
        "Run `polyglot-eval serve-ui --task I2 --data reports/artifacts/I2/data.json` → http://localhost:5174",
    ),
]

SPEC = TaskSpec(
    id="I2",
    slug="flow_trace",
    title="Request / Event Flow Trace + React UI",
    description="Trace the primary request flow → Mermaid sequenceDiagram + React timeline UI at localhost:5174.",
    system_prompt=_SYSTEM_PROMPT.format(
        contract="\n".join(f"- `{d.key}`: {d.label}" for d in _DELIVERABLES)
        + "\n- You MUST include at least one valid Mermaid diagram in `mermaid`."
    ),
    kickoff=_KICKOFF,
    allowed_tools=["Read", "Grep", "Glob", "Bash"],
    permission_mode="plan",
    writes_repo=False,
    deliverables=_DELIVERABLES,
    requires_mermaid=True,
)
