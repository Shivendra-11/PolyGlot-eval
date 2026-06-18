"""Repo-agnostic static analysis helpers for offline dashboard data generation."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

SKIP_DIRS = {
    "node_modules", ".git", "build", "dist", ".venv", "venv",
    "reports", "__pycache__", ".pytest_cache", "coverage", "examples",
}

SOURCE_SUFFIXES = {".js", ".jsx", ".ts", ".tsx", ".py", ".java", ".go", ".rs", ".prisma", ".sql"}


def walk_sources(repo: Path) -> list[Path]:
    files: list[Path] = []
    repo = repo.resolve()
    for p in repo.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(repo)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if p.suffix.lower() in SOURCE_SUFFIXES:
            files.append(p)
    return files


def _rel(repo: Path, path: Path) -> str:
    return str(path.relative_to(repo.resolve()))


def grep_routes(repo: Path) -> list[str]:
    routes: set[str] = set()
    patterns = [
        re.compile(r"""['"](/[^'"]+)['"]"""),
        re.compile(r"@(?:app|router)\.(?:get|post|put|delete|patch)\(['\"]([^'\"]+)"),
        re.compile(r"\.(?:get|post|put|delete|patch)\(['\"]([^'\"]+)"),
    ]
    for p in walk_sources(repo):
        text = p.read_text(encoding="utf-8", errors="ignore")
        for pat in patterns:
            for m in pat.finditer(text):
                route = m.group(1) if m.lastindex else m.group(0)
                if route.startswith("/") and len(route) < 120:
                    routes.add(route)
    return sorted(routes)[:50]


def grep_actions(repo: Path) -> list[str]:
    actions: list[str] = []
    for p in walk_sources(repo):
        if "action" not in str(p).lower() and p.suffix != ".py":
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        for m in re.finditer(r"export\s+(?:const|async function)\s+(\w+)", text):
            actions.append(f"{_rel(repo, p)}::{m.group(1)}")
        for m in re.finditer(r"^def\s+(\w+)\(", text, re.MULTILINE):
            if not m.group(1).startswith("_"):
                actions.append(f"{_rel(repo, p)}::{m.group(1)}")
    return sorted(set(actions))[:40]


def scan_entities(repo: Path) -> list[dict[str, Any]]:
    """Discover entities from classes, interfaces, contexts, SQL, and Prisma models."""
    repo = repo.resolve()
    entities: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add(name: str, source: Path, line: int, fields: list[str]) -> None:
        if name in seen or name.startswith("_"):
            return
        seen.add(name)
        cols = [
            {
                "name": f,
                "type": "string",
                "isPK": f in ("id", "uuid") or f.endswith("Id") and f == "id",
                "isFK": f.endswith("_id") or (f.endswith("Id") and f != "id"),
                "references": None,
            }
            for f in fields[:12]
        ] or [{"name": "id", "type": "string", "isPK": True, "isFK": False, "references": None}]
        entities.append({
            "name": name,
            "sourceFile": _rel(repo, source),
            "sourceLine": line,
            "columns": cols,
        })

    for p in walk_sources(repo):
        text = p.read_text(encoding="utf-8", errors="ignore")
        if p.suffix == ".py":
            for m in re.finditer(r"^class\s+(\w+)", text, re.MULTILINE):
                body = text[m.start(): m.start() + 800]
                fields = re.findall(r"^\s+(\w+)\s*[:=]", body, re.MULTILINE)
                add(m.group(1), p, text[: m.start()].count("\n") + 1, fields)
        elif p.suffix in {".js", ".jsx", ".ts", ".tsx"}:
            if "createContext" in text or "useState" in text:
                name = p.stem.replace("Context", "") or p.stem
                fields = re.findall(r"(\w+)\s*:", text[:2000])
                fields = [f for f in sorted(set(fields)) if f not in {"const", "return", "function", "type"}][:12]
                add(name or p.stem, p, 1, fields)
            for m in re.finditer(r"(?:interface|type)\s+(\w+)", text):
                add(m.group(1), p, text[: m.start()].count("\n") + 1, [])
        elif p.suffix == ".sql":
            for m in re.finditer(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)", text, re.I):
                add(m.group(1), p, text[: m.start()].count("\n") + 1, ["id"])
        elif p.suffix == ".prisma":
            for m in re.finditer(r"model\s+(\w+)\s*\{([^}]+)\}", text):
                fields = re.findall(r"^\s+(\w+)\s+", m.group(2), re.MULTILINE)
                add(m.group(1), p, text[: m.start()].count("\n") + 1, fields)

    return entities[:30]


def infer_relationships(entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    names = {e["name"] for e in entities}
    rels: list[dict[str, Any]] = []
    for e in entities:
        for col in e.get("columns", []):
            cname = col["name"]
            if not col.get("isFK"):
                continue
            target = cname.replace("_id", "").replace("Id", "")
            target = target[0].upper() + target[1:] if target else ""
            if target in names and target != e["name"]:
                rels.append({
                    "from": e["name"],
                    "to": target,
                    "type": "inferred",
                    "label": "references",
                    "sourceFile": e["sourceFile"],
                    "sourceLine": e["sourceLine"],
                })
    if len(rels) < 2 and len(entities) >= 2:
        for i in range(min(3, len(entities) - 1)):
            a, b = entities[i], entities[i + 1]
            rels.append({
                "from": a["name"],
                "to": b["name"],
                "type": "inferred",
                "label": "relates_to",
                "sourceFile": a["sourceFile"],
                "sourceLine": a["sourceLine"],
            })
    return rels[:20]


def find_entry_points(repo: Path) -> list[dict[str, Any]]:
    """Locate likely application entry files and handlers."""
    repo = repo.resolve()
    candidates: list[tuple[int, Path, str]] = []

    priority_names = {
        "main.py": 10, "app.py": 10, "server.py": 9, "server.js": 9,
        "index.js": 8, "index.ts": 8, "main.go": 10, "main.rs": 10,
    }
    for p in walk_sources(repo):
        score = priority_names.get(p.name, 0)
        if score:
            candidates.append((score, p, p.name))
        if p.name in {"routes.py", "routes.js", "router.py", "api.py"}:
            candidates.append((7, p, p.name))

    pkg = repo / "package.json"
    if pkg.is_file():
        try:
            data = json.loads(pkg.read_text(encoding="utf-8"))
            main = data.get("main") or (data.get("scripts") or {}).get("start", "")
            if main:
                main_path = repo / str(main).split()[0]
                if main_path.is_file():
                    candidates.append((9, main_path, main_path.name))
        except json.JSONDecodeError:
            pass

    candidates.sort(key=lambda x: -x[0])
    entries: list[dict[str, Any]] = []
    seen: set[str] = set()
    for _, p, _ in candidates:
        rel = _rel(repo, p)
        if rel in seen:
            continue
        seen.add(rel)
        text = p.read_text(encoding="utf-8", errors="ignore")
        funcs = re.findall(r"^(?:export\s+)?(?:async\s+)?function\s+(\w+)|^def\s+(\w+)", text, re.MULTILINE)
        fn = next((a or b for a, b in funcs if (a or b) not in ("main",)), funcs[0][0] or funcs[0][1] if funcs else p.stem)
        entries.append({"file": rel, "function": fn or p.stem, "line": 1, "description": f"Entry module {rel}"})
        if len(entries) >= 5:
            break
    return entries or [{"file": ".", "function": "main", "line": 1, "description": "Repository root"}]


def scan_flow_steps(repo: Path) -> list[dict[str, Any]]:
    """Build a trace timeline from entry points and exported handlers."""
    repo = repo.resolve()
    steps: list[dict[str, Any]] = []
    entries = find_entry_points(repo)
    routes = grep_routes(repo)

    for i, ep in enumerate(entries[:5], start=1):
        steps.append({
            "index": i,
            "file": ep["file"],
            "function": ep["function"],
            "line": ep.get("line", 1),
            "description": ep.get("description", "Application entry"),
            "ioType": "http_call" if ep["file"].endswith((".js", ".py")) else None,
        })

    for j, route in enumerate(routes[:8], start=len(steps) + 1):
        steps.append({
            "index": j,
            "file": entries[0]["file"] if entries else ".",
            "function": route,
            "line": 1,
            "description": f"Route handler {route}",
            "ioType": "http_call",
        })

    for p in walk_sources(repo):
        if len(steps) >= 15:
            break
        if p.suffix != ".py" or "test" in p.name:
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        for m in re.finditer(r"^def\s+(\w+)\(", text, re.MULTILINE):
            if m.group(1).startswith("_"):
                continue
            rel = _rel(repo, p)
            if any(s["file"] == rel and s["function"] == m.group(1) for s in steps):
                continue
            steps.append({
                "index": len(steps) + 1,
                "file": rel,
                "function": m.group(1),
                "line": text[: m.start()].count("\n") + 1,
                "description": f"Callable {m.group(1)}",
                "ioType": None,
            })
            if len(steps) >= 15:
                break

    for idx, s in enumerate(steps, start=1):
        s["index"] = idx
    return steps[:15]


def detect_test_command(repo: Path) -> str:
    pkg = repo / "package.json"
    if pkg.is_file():
        try:
            data = json.loads(pkg.read_text(encoding="utf-8"))
            scripts = data.get("scripts") or {}
            if "test" in scripts:
                return "npm test"
        except json.JSONDecodeError:
            pass
    if (repo / "pytest.ini").is_file() or (repo / "pyproject.toml").is_file():
        return "pytest -q"
    if (repo / "Cargo.toml").is_file():
        return "cargo test"
    return "pytest -q"


def find_primary_module(repo: Path) -> tuple[str, str]:
    """Return (file path, function name) for I3/I6 targeting."""
    entries = find_entry_points(repo)
    if entries:
        return entries[0]["file"], entries[0]["function"]
    sources = walk_sources(repo)
    if sources:
        p = sources[0]
        return _rel(repo, p), p.stem
    return "README.md", "main"


def detect_docker(repo: Path) -> dict[str, Any]:
    dockerfile = repo / "Dockerfile"
    compose = repo / "docker-compose.yml"
    image = repo.name.lower().replace("_", "-")
    port = 8080
    if dockerfile.is_file():
        text = dockerfile.read_text(encoding="utf-8", errors="ignore")
        m = re.search(r"EXPOSE\s+(\d+)", text)
        if m:
            port = int(m.group(1))
    return {
        "has_docker": dockerfile.is_file(),
        "dockerfile": dockerfile,
        "compose": compose,
        "image": f"{image}:local",
        "port": port,
    }


def build_er_mermaid(entities: list[dict[str, Any]], relationships: list[dict[str, Any]]) -> str:
    lines = ["erDiagram"]
    for e in entities:
        lines.append(f"    {e['name']} {{")
        for col in e["columns"][:8]:
            tag = " PK" if col.get("isPK") else (" FK" if col.get("isFK") else "")
            lines.append(f"        {col['type']} {col['name']}{tag}")
        lines.append("    }")
    for r in relationships:
        card = "||--o{" if r["type"] == "explicit" else "}o--o{"
        lines.append(f"    {r['from']} {card} {r['to']} : \"{r['label']}\"")
    return "\n".join(lines)


def build_sequence_mermaid(repo: Path, steps: list[dict[str, Any]], routes: list[str]) -> str:
    name = repo.name
    route = routes[0] if routes else "/"
    ep = steps[0] if steps else {"file": "app", "function": "main"}
    return f"""sequenceDiagram
    participant Client
    participant App as {name}
    participant Handler as {ep['function']}
    participant Store as Data Layer

    Client->>App: {route}
    App->>Handler: {ep['function']}()
    Handler->>Store: read/write
    Store-->>Handler: result
    Handler-->>App: response
    App-->>Client: 200 OK"""
