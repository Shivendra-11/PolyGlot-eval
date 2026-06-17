"""I4 — Polyglot Pair (FastAPI + Node.js + React UI)

Greenfield gated-write task. Creates a FastAPI currency-conversion microservice, a
companion Node.js CLI client, AND a React (Vite) frontend UI — all from scratch.
"""

from .base import Deliverable, TaskSpec

_SYSTEM_PROMPT = """\

You are a full-stack engineer building a greenfield polyglot micro-project: a Python FastAPI
service, a Node.js CLI client, AND a React (Vite) frontend UI. You have full write access to
the output artifacts directory.

## Your goal
Build the following from scratch, writing all files to `reports/artifacts/I4/` via
`mcp__report__save_artifact`:

### Service (Python / FastAPI)
- `service/main.py` — FastAPI app with a `POST /convert` endpoint.
  - Request body: `{{ "amount": float, "from": str, "to": str }}`
  - Response: `{{ "amount": float, "from": str, "to": str, "converted": float, "rate": float }}`
  - Hardcoded exchange rates table for at least: USD, EUR, GBP, JPY, INR, AUD, CAD.
  - Input validation via Pydantic: amount > 0, currency codes must be in the rates table.
  - Returns HTTP 422 for invalid input.
  - `GET /health` returns `{{ "status": "ok" }}`.
- `service/requirements.txt` — `fastapi`, `uvicorn[standard]`, `pydantic`.
- `service/test_service.py` — pytest tests covering: valid conversion, unknown currency 422,
  negative amount 422, /health endpoint.

### Client (Node.js CLI)
- `client/index.js` — executable Node.js CLI (`#!/usr/bin/env node`).
  - Usage: `node index.js <amount> <from> <to>`
  - Calls `POST http://localhost:8000/convert` and prints the result as a formatted table.
  - Handles HTTP errors and prints a friendly message.
- `client/package.json` — name, version, description, main, scripts (`test`).
- `client/test_client.sh` — a bash script that starts the service, calls the CLI with a few
  test cases, and verifies the output (exit-code based).

### React UI (Vite) — `ui/`
- `ui/package.json` — name, version, Vite + React deps, scripts: `dev`, `build`, `preview`.
- `ui/vite.config.js` — Vite config with `@vitejs/plugin-react`.
- `ui/index.html` — root HTML with `<div id="root">`.
- `ui/src/main.jsx` — ReactDOM.createRoot render.
- `ui/src/App.jsx` — Main component with:
  - Title: "Currency Converter"
  - Dropdowns for From/To currency (USD, EUR, GBP, JPY, INR, AUD, CAD)
  - Number input for amount
  - Convert button → calls `POST http://localhost:8000/convert`
  - Result card showing: `X USD = Y EUR (rate: Z)`
  - Loading state + error state
  - Dark glassmorphism theme: dark gradient background, purple accent (#6c63ff),
    card with backdrop blur, smooth button hover animation
- `ui/src/App.css` — All styles (dark theme, glassmorphism, gradients).
- CORS: the FastAPI service must allow `http://localhost:5173`.

### README
- `README.md` — **three-terminal** run instructions: Terminal 1 = backend, Terminal 2 = React UI, Terminal 3 = CLI client.

## Rules
1. Write all files using `mcp__report__save_artifact`. Do NOT use the Edit/Write built-in tools
   directly on the repo — the artifacts directory is your working area.
2. Bash is allowed to run tests. Use it to `pip install -r requirements.txt` in a temp venv,
   run `pytest`, then run `npm install` in the ui/ dir to verify it installs cleanly.
3. The exchange rates must be hardcoded — no external API calls.
4. The Pydantic model must reject invalid currencies with a clear error message.
5. The React UI must be visually premium — dark gradient background, glassmorphism card,
   purple accent, smooth animations. Plain/minimal styling is NOT acceptable.
6. Finish by calling `mcp__report__submit_report` with all required sections.
7. **Write dashboard data** — save `reports/artifacts/I4/data.json`:
   ```json
   {{
     "repoName": "<repo>",
     "generatedAt": "<ISO>",
     "status": "pass",
     "serviceSummary": "<FastAPI summary>",
     "clientSummary": "<Node CLI summary>",
     "uiSummary": "<React UI summary>",
     "stack": {{ "backend": "...", "client": "...", "ui": "..." }},
     "endpoints": [{{ "method": "POST", "path": "/convert", "request": {{}}, "response": {{}}, "errors": [] }}],
     "currencies": ["USD", "EUR"],
     "artifacts": ["service/main.py", "client/index.js", "ui/package.json"],
     "tests": {{ "service": {{ "command": "pytest", "passed": 4, "failed": 0 }}, "client": {{}}, "ui": {{}} }},
     "testOutput": "<pytest output excerpt>",
     "runInstructions": ["Terminal 1: uvicorn ...", "Terminal 2: npm run dev"],
     "architectureDiagram": "flowchart LR ...",
     "ports": {{ "api": 8000, "ui": 5173 }}
   }}
   ```

## Deliverable contract
{contract}
"""

_KICKOFF = """\
Please build the FastAPI + Node.js + React UI polyglot project from scratch.

Write all source files to reports/artifacts/I4/ using save_artifact. Run pytest for the
backend tests and npm install for the React UI to verify it installs cleanly.
Finally submit the report.
"""

_DELIVERABLES = [
    Deliverable(
        "service_summary",
        "Description of the FastAPI service: endpoint contract, rates table, validation rules, CORS config",
    ),
    Deliverable(
        "client_summary",
        "Description of the Node.js CLI: usage, how it calls the service, output format",
    ),
    Deliverable(
        "ui_summary",
        "Description of the React UI: features, how it calls the backend, how to run it (npm run dev → localhost:5173)",
    ),
    Deliverable(
        "service_test_output",
        "The exact pytest command and full test output for the service tests",
    ),
    Deliverable(
        "client_test_output",
        "The exact command and output for the client tests / scripted verify",
    ),
    Deliverable(
        "run_instructions",
        "Three-terminal run instructions: Terminal 1 = backend, Terminal 2 = React UI (localhost:5173), Terminal 3 = CLI client",
    ),
    Deliverable(
        "files_created",
        "List of every file saved as an artifact (relative paths under I4/)",
    ),
]

SPEC = TaskSpec(
    id="I4",
    slug="polyglot_pair",
    title="Polyglot Pair (FastAPI + Node.js + React UI)",
    description="Build a FastAPI backend, Node.js CLI, and React UI currency converter from scratch.",
    system_prompt=_SYSTEM_PROMPT.format(
        contract="\n".join(f"- `{d.key}`: {d.label}" for d in _DELIVERABLES)
    ),
    kickoff=_KICKOFF,
    allowed_tools=["Read", "Write", "Bash"],
    permission_mode="default",
    writes_repo=False,
    deliverables=_DELIVERABLES,
    requires_mermaid=False,
)
