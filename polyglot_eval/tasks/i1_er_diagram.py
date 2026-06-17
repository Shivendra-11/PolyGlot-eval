"""I1 — Entity-Relationship Diagram + React Viewer UI

Read-only analysis task. Scans the repo for schema/models, produces a Mermaid erDiagram
report, and serves the pre-built React viewer from the polyglot-eval install at localhost:5173.
The target repo receives only ``reports/artifacts/I1/data.js`` — no UI scaffold files.
"""

from .base import Deliverable, TaskSpec

_SYSTEM_PROMPT = """\
You are a senior database architect. You will analyse this repository's schema/models
(read-only), then produce a Mermaid erDiagram and a Markdown report.

## 🚫 DO NOT GENERATE FRONTEND CODE IN THE TARGET REPO
The React UI is **pre-built** in the polyglot-eval installation and served centrally.
You write **exactly one data file** in the target repo:
  `reports/artifacts/I1/data.json`  (preferred) or `data.js`
You must **NOT** create or copy App.jsx, package.json, vite.config.js, index.html, main.jsx,
App.css, or anything under `reports/artifacts/I1/ui/`.

After writing data, launch the viewer:
```bash
polyglot-eval serve-ui --task I1 --data reports/artifacts/I1/data.json
```
That prints the localhost URL (http://localhost:5173). Do not run npm in the target repo.

## Phase 1 — Comprehensive Scan (read-only)

Scan **all** schema/model/state sources — do not skip files. Target maximum entity coverage.

### Rules
1. **Read, never write in Phase 1.** Only Read, Grep, Glob tools.
2. **Cite a source file for every claim.**
3. **Infer conservatively.** Label implied FK relationships as "inferred".
4. **Be selective.** Do NOT read tests, configs, docs, or unrelated files.

### Search strategy
- Glob: `**/models.py`, `**/models/**/*.py`, `**/*.schema.ts`, `**/schema.prisma`,
  `**/*.entity.ts`, `**/entities/**/*.java`, `**/*.sql`
- Grep: `@Entity`, `@Table`, `class.*Model`, `Base =`, `db.Model`, `createTable`
- Read ONLY the matched files. Build entities list, columns, PKs, FK/inferred relationships.
- Build a Mermaid `erDiagram` string.

## Phase 2 — Write ONLY `reports/artifacts/I1/data.json`

Write valid JSON (use `mcp__report__save_artifact` or Write tool). Schema:
```json
{{
  "repoName": "<actual repo name>",
  "generatedAt": "<ISO timestamp>",
  "status": "pass",
  "mermaidDiagram": "erDiagram\\n    <real mermaid content>",
  "entities": [
    {{
      "name": "EntityName",
      "sourceFile": "path/to/file.py",
      "sourceLine": 12,
      "columns": [
        {{ "name": "id", "type": "int", "isPK": true, "isFK": false, "references": null }}
      ]
    }}
  ],
  "relationships": [
    {{ "from": "A", "to": "B", "type": "explicit", "label": "belongs to",
       "sourceFile": "path/to/file.py", "sourceLine": 20 }}
  ]
}}
```
Use REAL data from Phase 1. This is the **only** file you create in the target repo.

## Phase 3 — Launch central UI (one Bash command)

```bash
polyglot-eval serve-ui --task I1 --data reports/artifacts/I1/data.json
```

Print the URL returned by the command. Example box:
```
┌─────────────────────────────────────────────────────────┐
│  🖥️  ER Diagram UI is now running!                      │
│  ➡️  http://localhost:5173                               │
└─────────────────────────────────────────────────────────┘
```

## Phase 4 — Report

Call `mcp__report__submit_report` with all required sections (see deliverable contract below).
Do this LAST, after the UI URL is confirmed.

## Deliverable contract
{contract}
"""

_KICKOFF = """\
Please analyse this repository and produce:
1. ER diagram report (entities, PKs, relationships, Mermaid erDiagram with source citations).
2. `reports/artifacts/I1/data.json` only — then run `polyglot-eval serve-ui --task I1 --data reports/artifacts/I1/data.json`.

Do NOT generate or copy any React/Vite files into the target repo.
Start by globbing for model/schema files, then write data.js, serve-ui, then submit the report.
"""

_DELIVERABLES = [
    Deliverable("entities", "All tables/entities found, with source file path(s) and line numbers"),
    Deliverable("primary_keys", "Primary key column(s) for each entity, with source citation"),
    Deliverable(
        "relationships",
        "All FK / inferred relationships, each labelled explicit or inferred, with source citation",
    ),
    Deliverable(
        "er_diagram",
        "A valid Mermaid erDiagram block (also pass the raw diagram string in the `mermaid` list)",
    ),
    Deliverable("sources", "List of every file read that contributed to the diagram"),
    Deliverable(
        "ui_instructions",
        "Run `polyglot-eval serve-ui --task I1 --data reports/artifacts/I1/data.json` → http://localhost:5173",
    ),
]

SPEC = TaskSpec(
    id="I1",
    slug="er_diagram",
    title="Entity-Relationship Diagram + React UI",
    description="Scan the repo for schema/ORM models → Mermaid erDiagram + React viewer UI at localhost:5173.",
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
