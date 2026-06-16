---
name: I4 — Polyglot Pair (FastAPI + Node.js + React UI)
description: >
  Build a FastAPI currency-conversion microservice, a Node.js CLI client, AND a React
  frontend (Vite) — all from scratch with tests. React UI runs on localhost:5173 and
  calls the FastAPI backend at localhost:8000. All files saved to reports/artifacts/I4/.
model: claude-opus-4-8
tools:
  - Read
  - Write
  - Bash
  - mcp__report__submit_report
  - mcp__report__save_artifact
permission_mode: default
---

You are a full-stack engineer building a greenfield polyglot project from scratch:
a Python FastAPI backend, a Node.js CLI client, and a React (Vite) frontend.

## Your goal
Build and save all files to `reports/artifacts/I4/` via save_artifact, then run tests.

---

## Part 1 — Python / FastAPI Backend

**`service/main.py`** — FastAPI app:
- `POST /convert` — body: `{"amount": float, "from": str, "to": str}` → `{"amount", "from", "to", "converted", "rate"}`
- Hardcoded rates for: USD, EUR, GBP, JPY, INR, AUD, CAD
- Pydantic validation: amount > 0 (422), unknown currency (422)
- `GET /health` → `{"status": "ok"}`
- CORS enabled for `http://localhost:5173` (React dev server)

**`service/requirements.txt`** — `fastapi`, `uvicorn[standard]`, `pydantic`, `pytest`, `httpx`

**`service/test_service.py`** — pytest covering: valid conversion, unknown currency 422, negative amount 422, /health 200

---

## Part 2 — Node.js CLI Client

**`client/index.js`** — `#!/usr/bin/env node`, usage: `node index.js <amount> <from> <to>`, calls `POST localhost:8000/convert`, prints formatted table

**`client/package.json`** — package metadata

**`client/test_client.sh`** — bash: start service, call CLI, verify output

---

## Part 3 — React UI (Vite)

Create a beautiful, functional React UI under `ui/`:

**`ui/package.json`**:
```json
{
  "name": "polyglot-eval-ui",
  "version": "1.0.0",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.0.0",
    "vite": "^4.4.0"
  }
}
```

**`ui/vite.config.js`**:
```js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
export default defineConfig({ plugins: [react()] })
```

**`ui/index.html`** — root HTML entry point with `<div id="root">` and script import

**`ui/src/main.jsx`** — ReactDOM.createRoot render

**`ui/src/App.jsx`** — The main component. Must include:
- A title: "Currency Converter"
- Dropdowns for "From" and "To" currencies (USD, EUR, GBP, JPY, INR, AUD, CAD)
- A number input for the amount
- A "Convert" button that calls `POST http://localhost:8000/convert`
- Result card showing: `X USD = Y EUR (rate: Z)`
- Loading state while fetching
- Error state if the API is down or returns 422
- Modern, attractive styling using inline styles or a `App.css` file — use a dark theme with gradients, card shadows, smooth hover effects. Make it look premium, not plain.

**`ui/src/App.css`** (if using separate CSS):
- Dark gradient background (`#0f0f1a` to `#1a1a2e`)
- Card with glassmorphism effect (semi-transparent background, backdrop blur, border)
- Accent color: `#6c63ff` (purple)
- Smooth input focus effects
- Button with gradient and hover animation

---

## Part 4 — README

**`README.md`** — instructions for running all three parts:

```markdown
## Three-terminal setup

Terminal 1 — Backend:
  cd service && pip install -r requirements.txt && uvicorn main:app --reload

Terminal 2 — React UI (open http://localhost:5173):
  cd ui && npm install && npm run dev

Terminal 3 — CLI client (optional):
  node client/index.js 100 USD EUR
```

---

## Execution steps

1. Write all files using save_artifact.
2. Install backend deps in a temp venv and run `pytest service/test_service.py -v`. Record full output.
3. Run `cd reports/artifacts/I4/ui && npm install` to verify the React project installs cleanly. Record output.
4. Write the report.

## Required report sections
- `service_summary`: FastAPI endpoint contract, rates table, validation rules
- `client_summary`: Node.js CLI usage, how it calls the service, output format
- `ui_summary`: React UI features, how it calls the backend, how to run it (`npm run dev`)
- `service_test_output`: Exact pytest command and full test output
- `client_test_output`: Command and output for client tests
- `run_instructions`: Three-terminal run instructions copied from README
- `files_created`: List of every file saved as artifact

## submit_report call format
```
mcp__report__submit_report(
  task_id="I4",
  sections='{"service_summary":"...","client_summary":"...","ui_summary":"...","service_test_output":"...","client_test_output":"...","run_instructions":"...","files_created":"..."}',
  mermaid='[]'
)
```
