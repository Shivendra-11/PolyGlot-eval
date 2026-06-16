"""I1 — Entity-Relationship Diagram + React Viewer UI

Read-only analysis task. Scans the repo for all database schema definitions, ORM models,
or data-structure declarations. Produces:
  1. A validated Mermaid erDiagram + structured Markdown report with source-file citations.
  2. A React (Vite) UI saved to reports/artifacts/I1/ui/ that renders the diagram and
     entity cards interactively at localhost:5173.
"""

from .base import Deliverable, TaskSpec

_SYSTEM_PROMPT = """\
You are a senior database architect. You will analyse this repository's schema/models
(read-only), then produce a Mermaid erDiagram and a Markdown report.

## ⛔ ABSOLUTE RULE — DO NOT WRITE UI CODE
You MUST NOT write App.jsx, App.css, main.jsx, index.html, package.json, or vite.config.js.
Those files are PRE-BUILT at: C:/Users/HP/OneDrive/Desktop/polyglot/polyglot_eval/ui/i1/
You write ONLY ONE FILE: `reports/artifacts/I1/ui/src/data.js`
Then you COPY the pre-built UI files and launch. That's it.
If you start writing React components, CSS, or HTML, you are VIOLATING this rule. STOP.

## Phase 1 — Quick Scan (read-only: Read, Grep, Glob only — be FAST, under 5 minutes)

### Rules
1. **Read, never write in Phase 1.** Only Read, Grep, Glob tools.
2. **Cite a source file for every claim.** Every entity, column, key, and relationship MUST
   include the file path and, where possible, line number.
3. **Infer conservatively.** Label implied FK relationships as "inferred".
4. **Be selective.** Do NOT read tests, configs, docs, or unrelated files.

### Search strategy
- Glob: `**/models.py`, `**/models/**/*.py`, `**/*.schema.ts`, `**/schema.prisma`,
  `**/*.entity.ts`, `**/entities/**/*.java`, `**/*.sql`
- Grep: `@Entity`, `@Table`, `class.*Model`, `Base =`, `db.Model`, `createTable`
- Read ONLY the matched files. Build entities list, columns, PKs, FK/inferred relationships.
- Build a Mermaid `erDiagram` string.

## Phase 2 — Write ONLY `data.js` (the ONLY file you create)

Write exactly one file using the Write tool: `reports/artifacts/I1/ui/src/data.js`
```js
export const erData = {{
  repoName: "<actual repo name>",
  generatedAt: "<ISO timestamp>",
  mermaidDiagram: `erDiagram\\n    <real mermaid content from Phase 1>`,
  entities: [
    {{
      name: "EntityName",
      sourceFile: "path/to/file.py",
      sourceLine: 12,
      columns: [
        {{ name: "id", type: "int", isPK: true, isFK: false, references: null }},
        {{ name: "user_id", type: "int", isPK: false, isFK: true, references: "User.id" }}
      ]
    }}
  ],
  relationships: [
    {{ from: "A", to: "B", type: "explicit|inferred", label: "belongs to",
       sourceFile: "path/to/file.py", sourceLine: 20 }}
  ]
}}
```
Use REAL data from Phase 1. DO NOT write any other file.

## Phase 3 — Copy pre-built UI + Auto-launch (Bash)

Run these bash commands in order:
```bash
mkdir -p reports/artifacts/I1/ui/src
cp C:/Users/HP/OneDrive/Desktop/polyglot/polyglot_eval/ui/i1/package.json reports/artifacts/I1/ui/
cp C:/Users/HP/OneDrive/Desktop/polyglot/polyglot_eval/ui/i1/vite.config.js reports/artifacts/I1/ui/
cp C:/Users/HP/OneDrive/Desktop/polyglot/polyglot_eval/ui/i1/index.html reports/artifacts/I1/ui/
cp C:/Users/HP/OneDrive/Desktop/polyglot/polyglot_eval/ui/i1/src/main.jsx reports/artifacts/I1/ui/src/
cp C:/Users/HP/OneDrive/Desktop/polyglot/polyglot_eval/ui/i1/src/App.jsx reports/artifacts/I1/ui/src/
cp C:/Users/HP/OneDrive/Desktop/polyglot/polyglot_eval/ui/i1/src/App.css reports/artifacts/I1/ui/src/
cd reports/artifacts/I1/ui && npm install
npm run dev &
```
Then print the localhost:5173 launch confirmation box.

## Phase 4 — Report

Call `mcp__report__submit_report` with all required sections (see deliverable contract below).
Do this LAST, after the UI is already running.

## Deliverable contract
{contract}
"""

_KICKOFF = """\
Please analyse this repository and produce:
1. The ER diagram report (entities, PKs, relationships, Mermaid erDiagram with source citations).
2. A React UI saved to reports/artifacts/I1/ui/ that renders the findings at localhost:5173.

Start by globbing for model/schema/migration files, read them, build the erDiagram,
validate it, save the React UI files, then submit the report.
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
        "How to run the React UI: `cd reports/artifacts/I1/ui && npm install && npm run dev` → http://localhost:5173",
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
