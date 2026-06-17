"""I5 — Dockerize (Backend + React UI)

Gated-write task. Packages both the FastAPI backend AND the React UI (from I4) into
Docker containers orchestrated by docker-compose. Backend on port 8000, React served
by Nginx on port 3000. Validates both containers end-to-end.
"""

from .base import Deliverable, TaskSpec

_SYSTEM_PROMPT = """\
You are a DevOps engineer Dockerising a full-stack application: a FastAPI backend and
a React (Vite) frontend. You will create two containers wired by docker-compose.

## Your goal
Produce the following under `reports/artifacts/I5/`, then build, run, and verify:

### `Dockerfile.backend`
- Base: `python:3.11-slim`
- Non-root USER
- Layer-efficient COPY: requirements → pip install → source
- EXPOSE 8000
- HEALTHCHECK: `curl -f http://localhost:8000/health || exit 1`
- CMD: `uvicorn main:app --host 0.0.0.0 --port 8000`

### `Dockerfile.frontend` (multi-stage)
- Stage 1 (`node:18-alpine` as builder): `npm install && npm run build`
- Stage 2 (`nginx:alpine`): copy `dist/` → `/usr/share/nginx/html`
- Copy `nginx.conf` into the image
- EXPOSE 3000
- HEALTHCHECK: `curl -f http://localhost:3000 || exit 1`

### `nginx.conf`
- Listen on port 3000
- Serve `/usr/share/nginx/html` for the React app
- Proxy `/api/` → `http://backend:8000/` (strips prefix so React can call `/api/convert`)

### `docker-compose.yml`
```yaml
version: "3.9"
services:
  backend:
    build:
      context: ../I4/service
      dockerfile: ../../I5/Dockerfile.backend
    ports:
      - "8000:8000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 5s
      retries: 3
  frontend:
    build:
      context: ../I4/ui
      dockerfile: ../../I5/Dockerfile.frontend
    ports:
      - "3000:3000"
    depends_on:
      backend:
        condition: service_healthy
```

### `README_docker.md`
- Single command: `docker-compose up --build`
- Access: React UI → http://localhost:3000, API → http://localhost:8000
- Stop: `docker-compose down`

## Execution steps
1. Write all files via save_artifact.
2. `docker-compose build` from I5 dir. Capture full output.
3. `docker-compose up -d`. Capture output.
4. `curl -f http://localhost:8000/health` → capture response.
5. `curl -f http://localhost:3000` → capture response (should be HTML).
6. `docker-compose down`. Capture output.

If docker is unavailable: document this, show all files with expected output.

## Rules
1. Never `docker push`. Never push to any registry.
2. All files written via save_artifact under `reports/artifacts/I5/`.
3. **Write dashboard data** — save `reports/artifacts/I5/data.json`:
   ```json
   {{
     "repoName": "<repo>",
     "generatedAt": "<ISO>",
     "status": "pass",
     "strategy": "<docker approach>",
     "dockerFiles": [{{ "path": "Dockerfile", "role": "...", "baseImage": "node:18-alpine" }}],
     "compose": {{ "services": [{{ "name": "app", "ports": ["8080:8080"] }}] }},
     "healthChecks": [{{ "name": "API", "url": "http://localhost:8080/health", "status": "ok", "latencyMs": 12 }}],
     "healthCheck": {{ "url": "http://localhost:8080/health", "status": "ok", "response": "..." }},
     "ports": {{ "frontend": 8080 }},
     "buildSteps": ["docker build -t app:local ."],
     "buildOutput": "<docker build excerpt>",
     "runOutput": "<docker run excerpt>",
     "runInstructions": ["docker build ...", "docker run ...", "curl -f ..."],
     "filesCreated": ["Dockerfile", "docker-compose.yml"],
     "resourceLimits": {{ "memory": "512Mi", "cpu": "0.5" }}
   }}
   ```
4. Finish by calling `mcp__report__submit_report` with all required sections.

## Deliverable contract
{contract}
"""

_KICKOFF = """\
Please Dockerise both the FastAPI backend and the React UI from reports/artifacts/I4/.

Create Dockerfile.backend, Dockerfile.frontend (multi-stage), nginx.conf,
docker-compose.yml, and README_docker.md. Then build, run, and verify both containers.
Submit the report when done.
"""

_DELIVERABLES = [
    Deliverable(
        "backend_dockerfile",
        "Dockerfile.backend content (inline) and explanation of each key instruction",
    ),
    Deliverable(
        "frontend_dockerfile",
        "Dockerfile.frontend content (inline) — explain the multi-stage build and Nginx proxy",
    ),
    Deliverable(
        "compose_summary",
        "docker-compose.yml content and explanation of how the two containers communicate",
    ),
    Deliverable(
        "build_output",
        "Exact `docker-compose build` command and full terminal output (last 50 lines if long)",
    ),
    Deliverable(
        "run_output",
        "Exact `docker-compose up -d` command, container IDs, and startup logs",
    ),
    Deliverable(
        "healthcheck_output",
        "Both curl commands and their responses: backend /health and frontend / (HTML)",
    ),
    Deliverable(
        "run_instructions",
        "One-command setup + access URLs: React UI at localhost:3000, API at localhost:8000",
    ),
    Deliverable(
        "files_created",
        "List of every file saved as an artifact (relative paths under I5/)",
    ),
]

SPEC = TaskSpec(
    id="I5",
    slug="dockerize",
    title="Dockerize (Backend + React UI)",
    description="Dockerize both FastAPI backend and React UI with docker-compose. Backend on :8000, UI served by Nginx on :3000.",
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
