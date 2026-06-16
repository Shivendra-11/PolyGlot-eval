"""Custom MCP report tools exposed to all subagents.

Three tools:
  submit_report   — validates deliverable sections against the task contract, then writes
                    reports/<task_id>.md.
  save_artifact   — writes a file under reports/artifacts/<task_id>/...
  check_mermaid   — validates a Mermaid diagram (uses mmdc if available, else structural lint).

Register the server in the orchestrator with:
    server, tools = create_report_mcp_server(reports_dir, task_specs)
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_report(path: Path, task_id: str, sections: dict[str, str], mermaid: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = [f"# {task_id} Report\n"]

    for key, content in sections.items():
        lines.append(f"\n## {key}\n\n{content}\n")

    if mermaid:
        lines.append("\n## Diagrams\n")
        for diagram in mermaid:
            lines.append(f"\n```mermaid\n{diagram.strip()}\n```\n")

    path.write_text("\n".join(lines), encoding="utf-8")


def _structural_lint(diagram: str) -> list[str]:
    """Fallback linter when mmdc is not available."""
    errors: list[str] = []
    first_line = diagram.strip().splitlines()[0].strip() if diagram.strip() else ""
    valid_headers = {"erDiagram", "sequenceDiagram", "graph", "flowchart", "classDiagram",
                     "stateDiagram", "gantt", "pie", "journey", "gitgraph"}
    if not any(first_line.startswith(h) for h in valid_headers):
        errors.append(
            f"First line '{first_line}' is not a recognised Mermaid diagram header. "
            f"Expected one of: {', '.join(sorted(valid_headers))}"
        )
    # Check balanced braces
    if diagram.count("{") != diagram.count("}"):
        errors.append("Unbalanced curly braces { } in diagram.")
    if diagram.count("[") != diagram.count("]"):
        errors.append("Unbalanced square brackets [ ] in diagram.")
    return errors


def _validate_mermaid(diagram: str) -> list[str]:
    """Validate a Mermaid diagram. Uses mmdc if on PATH, else structural lint."""
    mmdc = shutil.which("mmdc")
    if mmdc:
        try:
            with tempfile.NamedTemporaryFile(suffix=".mmd", mode="w", delete=False, encoding="utf-8") as f:
                f.write(diagram)
                tmp_in = f.name
            tmp_out = tmp_in.replace(".mmd", ".svg")
            result = subprocess.run(
                [mmdc, "-i", tmp_in, "-o", tmp_out],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode != 0:
                return [f"mmdc error: {result.stderr.strip()}"]
            return []
        except Exception as exc:
            return [f"mmdc check failed: {exc}"]
        finally:
            for p in [tmp_in, tmp_out]:
                try:
                    os.unlink(p)
                except OSError:
                    pass
    else:
        return _structural_lint(diagram)


# ---------------------------------------------------------------------------
# Tool implementations (called by the MCP server)
# ---------------------------------------------------------------------------


def submit_report(
    task_id: str,
    sections: dict[str, Any],
    mermaid: list[str],
    *,
    reports_dir: Path,
    required_section_keys: list[str],
    requires_mermaid: bool,
) -> str:
    """Validate deliverable contract and write the report file.

    Returns a success string or raises ValueError with a descriptive message.
    """
    # 1. Validate required sections
    missing = [k for k in required_section_keys if not sections.get(k, "").strip()]
    if missing:
        raise ValueError(
            f"Report rejected — the following required sections are missing or empty: "
            f"{', '.join(missing)}. Fill them in and resubmit."
        )

    # 2. Validate mermaid requirement
    if requires_mermaid and not mermaid:
        raise ValueError(
            "Report rejected — this task requires at least one Mermaid diagram in the "
            "`mermaid` list. Add the diagram and resubmit."
        )

    # 3. Validate each mermaid diagram
    if mermaid:
        for i, diagram in enumerate(mermaid):
            errors = _validate_mermaid(diagram)
            if errors:
                raise ValueError(
                    f"Report rejected — Mermaid diagram {i+1} has errors: "
                    + "; ".join(errors)
                    + ". Fix and resubmit."
                )

    # 4. Write report
    report_path = reports_dir / f"{task_id}.md"
    _write_report(report_path, task_id, sections, mermaid)
    return f"Report written to {report_path}"


def save_artifact(
    task_id: str,
    rel_path: str,
    content: str,
    *,
    reports_dir: Path,
) -> str:
    """Write a file under reports/artifacts/<task_id>/<rel_path>."""
    artifact_path = reports_dir / "artifacts" / task_id / rel_path
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(content, encoding="utf-8")
    return f"Artifact saved to {artifact_path}"


def check_mermaid(diagram: str) -> str:
    """Validate a Mermaid diagram string. Returns 'OK' or a list of errors."""
    errors = _validate_mermaid(diagram)
    if errors:
        return "ERRORS:\n" + "\n".join(f"- {e}" for e in errors)
    return "OK — diagram is valid."


# ---------------------------------------------------------------------------
# MCP server factory
# ---------------------------------------------------------------------------


def create_report_mcp_server(reports_dir: Path, task_specs: dict):
    """Create and return an SDK MCP server with the three report tools bound to task_specs.

    Returns (server, tools_list) where tools_list contains the callable tool objects.
    Imported lazily so the module can be used without the SDK installed (e.g. in tests).
    """
    try:
        from claude_agent_sdk import tool, create_sdk_mcp_server
    except ImportError:
        raise ImportError(
            "claude-agent-sdk is required to run polyglot-eval. "
            "Install it with: pip install claude-agent-sdk"
        )

    @tool
    def submit_report_tool(task_id: str, sections: str, mermaid: str) -> str:
        """Submit the final structured report for a task.

        Args:
            task_id: The task ID, e.g. 'I1'.
            sections: JSON object mapping section keys to their content strings.
            mermaid: JSON array of Mermaid diagram strings (can be empty list '[]').
        """
        try:
            sections_dict: dict[str, str] = json.loads(sections)
            mermaid_list: list[str] = json.loads(mermaid)
        except json.JSONDecodeError as exc:
            return f"ERROR: Invalid JSON — {exc}"

        spec = task_specs.get(task_id)
        if spec is None:
            return f"ERROR: Unknown task_id '{task_id}'."

        try:
            return submit_report(
                task_id=task_id,
                sections=sections_dict,
                mermaid=mermaid_list,
                reports_dir=reports_dir,
                required_section_keys=spec.required_section_keys,
                requires_mermaid=spec.requires_mermaid,
            )
        except ValueError as exc:
            return f"ERROR: {exc}"

    @tool
    def save_artifact_tool(task_id: str, rel_path: str, content: str) -> str:
        """Save a file as an artifact under reports/artifacts/<task_id>/<rel_path>.

        Args:
            task_id: The task ID, e.g. 'I4'.
            rel_path: Relative path for the artifact, e.g. 'service/main.py'.
            content: The full text content to write.
        """
        return save_artifact(task_id=task_id, rel_path=rel_path, content=content, reports_dir=reports_dir)

    @tool
    def check_mermaid_tool(diagram: str) -> str:
        """Validate a Mermaid diagram string before submitting the report.

        Args:
            diagram: The full Mermaid diagram text (including the header line).
        """
        return check_mermaid(diagram)

    server = create_sdk_mcp_server(
        "report",
        tools=[submit_report_tool, save_artifact_tool, check_mermaid_tool],
    )
    return server, [submit_report_tool, save_artifact_tool, check_mermaid_tool]
