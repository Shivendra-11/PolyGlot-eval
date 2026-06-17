"""Build combined dashboard data from per-task artifacts in a target repo."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_PACKAGE_ROOT = Path(__file__).resolve().parent.parent


TASK_META = {
    "I1": {
        "title": "ER Diagram",
        "slug": "er_diagram",
        "icon": "🗄️",
        "mode": "read-only",
        "export": "erData",
    },
    "I2": {
        "title": "Flow Trace",
        "slug": "flow_trace",
        "icon": "🔀",
        "mode": "read-only",
        "export": "traceData",
    },
    "I3": {
        "title": "Safe Change",
        "slug": "safe_change",
        "icon": "✏️",
        "mode": "writes-repo",
        "export": "i3Data",
    },
    "I4": {
        "title": "Polyglot Pair",
        "slug": "polyglot_pair",
        "icon": "🔗",
        "mode": "creates-artifacts",
        "export": "i4Data",
    },
    "I5": {
        "title": "Dockerize",
        "slug": "dockerize",
        "icon": "🐳",
        "mode": "creates-artifacts",
        "export": "i5Data",
    },
    "I6": {
        "title": "Bug Diagnosis",
        "slug": "bug_diagnosis",
        "icon": "🐛",
        "mode": "writes-repo",
        "export": "i6Data",
    },
}


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _load_js_export(path: Path, export_name: str) -> dict[str, Any] | None:
    """Best-effort parse of ``export const name = {...}`` from a data.js file."""
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8")
    pattern = rf"export\s+const\s+{re.escape(export_name)}\s*=\s*(\{{[\s\S]*?\}})\s*;?\s*$"
    match = re.search(pattern, text, re.MULTILINE)
    if not match:
        return None
    blob = match.group(1)
    blob = re.sub(r"`([^`]*)`", lambda m: json.dumps(m.group(1)), blob)
    blob = re.sub(r",\s*([}\]])", r"\1", blob)
    blob = re.sub(r"(\w+)\s*:", r'"\1":', blob)
    blob = blob.replace("'", '"')
    try:
        return json.loads(blob)
    except json.JSONDecodeError:
        return {"_raw": text[:4000], "_parseError": True}


def load_task_data(repo: Path, task_id: str) -> dict[str, Any] | None:
    """Load task payload from ``reports/artifacts/<ID>/data.json`` or legacy ``data.js``."""
    meta = TASK_META[task_id]
    artifact_dir = repo / "reports" / "artifacts" / task_id
    data = _load_json(artifact_dir / "data.json")
    if data is not None:
        return data
    return _load_js_export(artifact_dir / "data.js", meta["export"])


def _infer_status(task_id: str, repo: Path, payload: dict[str, Any] | None) -> str:
    if payload is not None:
        return payload.get("status", "pass")
    report = repo / "reports" / f"{task_id}_{TASK_META[task_id]['slug']}.md"
    if report.is_file():
        return "pass"
    return "skipped"


def _task_summary(task_id: str, payload: dict[str, Any] | None, status: str) -> str:
    if payload is None:
        return "Not run" if status == "skipped" else "Report available"
    if task_id == "I1":
        n = len(payload.get("entities", []))
        return f"{n} entities mapped"
    if task_id == "I2":
        n = len(payload.get("steps", []))
        return f"{n} steps traced · {payload.get('tracedFlow', '')}"
    if task_id == "I3":
        title = payload.get("changeTitle") or payload.get("changeDescription") or "Change applied"
        stats = payload.get("diffStats") or {}
        n = stats.get("filesTouched") or len(payload.get("filesChanged") or [])
        return f"{title[:60]} · {n} files · {payload.get('testResult', '?')}"
    if task_id == "I4":
        eps = len(payload.get("endpoints") or [])
        arts = len(payload.get("artifacts") or [])
        return f"{eps} endpoints · {arts} artifacts · polyglot stack"
    if task_id == "I5":
        checks = payload.get("healthChecks") or []
        ok = sum(1 for c in checks if c.get("status") == "ok")
        return f"{ok}/{len(checks) or 1} health checks · {payload.get('strategy', 'Docker')[:40]}"
    if task_id == "I6":
        sev = payload.get("severity", "")
        rc = payload.get("rootCause") or {}
        fn = rc.get("function") or rc.get("file") or "diagnosed"
        return f"{sev} · {fn} · {payload.get('verification', {}).get('result', '?')}"
    return "Complete"


def build_dashboard_data(repo: Path) -> dict[str, Any]:
    """Aggregate all task artifacts into a single dashboard payload."""
    repo = repo.resolve()
    repo_name = repo.name
    generated_at = datetime.now(timezone.utc).isoformat()

    for tid in TASK_META:
        payload = load_task_data(repo, tid)
        if payload and payload.get("repoName"):
            repo_name = payload["repoName"]
            break

    tasks_summary = []
    task_payloads: dict[str, Any | None] = {}

    passed = failed = skipped = 0
    for task_id, meta in TASK_META.items():
        payload = load_task_data(repo, task_id)
        status = _infer_status(task_id, repo, payload)
        task_payloads[task_id.lower()] = payload

        if status == "pass":
            passed += 1
        elif status == "fail":
            failed += 1
        else:
            skipped += 1

        tasks_summary.append(
            {
                "id": task_id,
                "title": meta["title"],
                "icon": meta["icon"],
                "mode": meta["mode"],
                "status": status,
                "summary": _task_summary(task_id, payload, status),
                "reportPath": f"reports/{task_id}_{meta['slug']}.md",
                "hasData": payload is not None,
            }
        )

    summary_path = repo / "reports" / "SUMMARY.md"
    return {
        "repoName": repo_name,
        "repoPath": str(repo),
        "generatedAt": generated_at,
        "stats": {
            "total": len(TASK_META),
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
        },
        "tasks": tasks_summary,
        "i1": task_payloads.get("i1"),
        "i2": task_payloads.get("i2"),
        "i3": task_payloads.get("i3"),
        "i4": task_payloads.get("i4"),
        "i5": task_payloads.get("i5"),
        "i6": task_payloads.get("i6"),
        "hasSummary": summary_path.is_file(),
    }


def write_dashboard_js(repo: Path, dest: Path) -> dict[str, Any]:
    """Build dashboard data and write ``export const dashboardData = ...`` to *dest*."""
    data = build_dashboard_data(repo)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(
        f"export const dashboardData = {json.dumps(data, indent=2)};\n",
        encoding="utf-8",
    )
    return data


def write_task_js_from_json(json_path: Path, export_name: str, dest: Path) -> None:
    """Convert a task ``data.json`` into a Vite ``data.js`` module."""
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(
        f"export const {export_name} = {json.dumps(payload, indent=2)};\n",
        encoding="utf-8",
    )
