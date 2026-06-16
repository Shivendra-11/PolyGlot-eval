"""I2 — Flow Trace + React Viewer UI

Read-only analysis task. Traces the primary request/event path end-to-end. Produces:
  1. A Mermaid sequenceDiagram + step-by-step Markdown report with source-file citations.
  2. A React (Vite) UI saved to reports/artifacts/I2/ui/ that renders the trace as an
     interactive timeline + sequence diagram at localhost:5174.
"""

from .base import Deliverable, TaskSpec

_SYSTEM_PROMPT = """\
You are a senior software engineer performing a deep code trace. You will trace the most
important request/event flow (read-only), then produce a Mermaid sequenceDiagram and a
Markdown report.

## 🚫 SYSTEM ENFORCEMENT — AUTO-DENIED WRITES
You MUST NOT write App.jsx, App.css, main.jsx, index.html, package.json, or vite.config.js.
Those files are PRE-BUILT at: C:/Users/HP/OneDrive/Desktop/polyglot/polyglot_eval/ui/i2/
You write ONLY ONE FILE: `reports/artifacts/I2/ui/src/data.js`
Then you COPY the pre-built UI files and launch. That's it.
If you attempt to write App.jsx, App.css, main.jsx, index.html, package.json, or vite.config.js
the permission system will AUTOMATICALLY DENY the write with an error. It will not succeed.
Do NOT try. Just write data.js and use `cp` to copy the rest.

## Phase 1 — Quick Trace (read-only: Read, Grep, Glob only — be FAST, under 5 minutes)

### Rules
1. **Read, never write in Phase 1.**
2. **Cite file + function for every step.** Never say "the code does X" without a file citation.
3. **Flag uncertainty.** Dynamic dispatch, DI containers, runtime plugins → say so.
4. **Identify all external I/O.** DB queries, HTTP calls, queue messages, file writes, cache ops.
5. **Be selective.** Do NOT deep-dive into utility files, tests, or configs.

### Trace strategy
- Entry point: grep for `@app.get`, `@app.post`, `router.`, `addEventListener`, `main(`
- If the kickoff specifies an endpoint/function, trace that. Otherwise auto-detect.
- Follow the call chain file by file (max 10-15 files).
- Mark every external I/O interaction as a distinct step.

## Phase 2 — Write ONLY `data.js` (the ONLY file you create)

Write exactly one file using the Write tool: `reports/artifacts/I2/ui/src/data.js`
```js
export const traceData = {{
  repoName: "<actual repo name>",
  tracedFlow: "<name of traced endpoint/event>",
  generatedAt: "<ISO timestamp>",
  mermaidDiagram: `sequenceDiagram\\n    <actual mermaid content>`,
  entryPoint: {{
    file: "app/routes/orders.py", function: "create_order", line: 42,
    description: "...", registeredAs: "@router.post('/orders')"
  }},
  steps: [
    {{ index: 1, file: "...", function: "...", line: 42,
       description: "...", ioType: null }},
    {{ index: 2, file: "...", function: "...", line: 18,
       description: "...", ioType: "db_write" }}
  ],
  externalDeps: [
    {{ name: "Stripe API", file: "...", line: 33, description: "..." }}
  ],
  sideEffects: [
    {{ type: "db_write", file: "...", line: 55, description: "INSERT into orders" }},
    {{ type: "queue_publish", file: "...", line: 80, description: "Kafka order.created" }}
  ],
  uncertainty: [
    {{ description: "Plugin hook — runtime dispatch, target unknown", file: "...", line: 92 }}
  ]
}}
```
ioType values: `"db_write"`, `"db_read"`, `"http_call"`, `"queue_publish"`, `"queue_consume"`,
`"file_write"`, `"cache_set"`, `null` (for pure code steps).
Use REAL data from Phase 1. DO NOT write any other file.

## Phase 3 — Copy pre-built UI + Auto-launch (Bash)

Run these bash commands in order:
```bash
mkdir -p reports/artifacts/I2/ui/src
cp C:/Users/HP/OneDrive/Desktop/polyglot/polyglot_eval/ui/i2/package.json reports/artifacts/I2/ui/
cp C:/Users/HP/OneDrive/Desktop/polyglot/polyglot_eval/ui/i2/vite.config.js reports/artifacts/I2/ui/
cp C:/Users/HP/OneDrive/Desktop/polyglot/polyglot_eval/ui/i2/index.html reports/artifacts/I2/ui/
cp C:/Users/HP/OneDrive/Desktop/polyglot/polyglot_eval/ui/i2/src/main.jsx reports/artifacts/I2/ui/src/
cp C:/Users/HP/OneDrive/Desktop/polyglot/polyglot_eval/ui/i2/src/App.jsx reports/artifacts/I2/ui/src/
cp C:/Users/HP/OneDrive/Desktop/polyglot/polyglot_eval/ui/i2/src/App.css reports/artifacts/I2/ui/src/
cd reports/artifacts/I2/ui && npm install
npm run dev &
```
Then print the localhost:5174 launch confirmation box.

## Phase 4 — Report

Call `mcp__report__submit_report` LAST, after the UI is already running.

## Deliverable contract
{contract}
"""

_KICKOFF = """\
Please trace the primary request/event flow through this repository.

REMINDER: You write ONLY `data.js`. Do NOT write App.jsx, App.css, or any other UI file.
The React UI is pre-built — you copy it from C:/Users/HP/OneDrive/Desktop/polyglot/polyglot_eval/ui/i2/.

Steps:
1. Quick scan: find the main entry point and trace the call chain (read-only, be fast).
2. Write `reports/artifacts/I2/ui/src/data.js` with real trace data.
3. Copy the pre-built UI files (bash cp commands).
4. Run npm install && npm run dev to auto-launch at localhost:5174.
5. Submit the report last.
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
        "How to run the React UI: `cd reports/artifacts/I2/ui && npm install && npm run dev` → http://localhost:5174",
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
