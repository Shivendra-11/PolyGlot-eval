"""Orchestrator — validates options, selects tasks, and runs each as a subagent.

Public API:
    run(repo, task_ids, out_dir, autonomy, model) -> OrchestratorResult
"""

from __future__ import annotations

import asyncio
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from .config import Autonomy, resolve_model
from .permissions import make_permission_handler, validate_repo_state
from .tasks.registry import TASK_REGISTRY, get_task
from .tasks.base import TaskSpec


@dataclass
class TaskResult:
    task_id: str
    title: str
    status: str  # "pass" | "fail" | "skipped"
    report_path: Optional[Path] = None
    error: Optional[str] = None
    duration_seconds: float = 0.0


@dataclass
class OrchestratorResult:
    repo: Path
    tasks_run: list[TaskResult] = field(default_factory=list)
    summary_path: Optional[Path] = None

    @property
    def passed(self) -> list[TaskResult]:
        return [t for t in self.tasks_run if t.status == "pass"]

    @property
    def failed(self) -> list[TaskResult]:
        return [t for t in self.tasks_run if t.status == "fail"]


def _resolve_task_ids(task_ids: list[str]) -> list[str]:
    """Expand 'all' and validate IDs. Returns ordered list."""
    if not task_ids or task_ids == ["all"]:
        return list(TASK_REGISTRY.keys())
    resolved = []
    for tid in task_ids:
        tid = tid.upper()
        if tid not in TASK_REGISTRY:
            raise ValueError(
                f"Unknown task ID '{tid}'. Valid options: {', '.join(TASK_REGISTRY)} or 'all'."
            )
        if tid not in resolved:
            resolved.append(tid)
    # Sort in registry order
    order = list(TASK_REGISTRY.keys())
    return sorted(resolved, key=lambda t: order.index(t))


async def _run_single_task(
    spec: TaskSpec,
    repo: Path,
    reports_dir: Path,
    autonomy: Autonomy,
    model: str,
    mcp_server,
) -> TaskResult:
    """Run one task as a Claude subagent and return the result."""
    try:
        from claude_agent_sdk import query, ClaudeAgentOptions
    except ImportError:
        return TaskResult(
            task_id=spec.id,
            title=spec.title,
            status="fail",
            error="claude-agent-sdk is not installed. Run: pip install claude-agent-sdk",
        )

    start = datetime.now()
    permission_handler = make_permission_handler(autonomy, repo, task_id=spec.id)

    print(f"\n{'='*60}")
    print(f"  Running {spec.id}: {spec.title}")
    print(f"  Repo  : {repo}")
    print(f"  Model : {model}")
    print(f"  Mode  : {autonomy.value}")
    print(f"{'='*60}")

    try:
        options = ClaudeAgentOptions(
            cwd=str(repo),
            system_prompt=spec.system_prompt,
            allowed_tools=spec.effective_allowed_tools(),
            permission_mode=spec.permission_mode,
            can_use_tool=permission_handler,
            mcp_servers={"report": mcp_server} if mcp_server else {},
            model=model,
        )

        async for event in query(prompt=spec.kickoff, options=options):
            # Stream progress to stdout
            if hasattr(event, "type"):
                if event.type == "assistant":
                    for block in getattr(event.message, "content", []):
                        if hasattr(block, "text"):
                            print(block.text, end="", flush=True)
                elif event.type == "result":
                    print(f"\n\n✓ {spec.id} completed.")

        duration = (datetime.now() - start).total_seconds()
        report_path = reports_dir / f"{spec.id}_{spec.slug}.md"

        return TaskResult(
            task_id=spec.id,
            title=spec.title,
            status="pass" if report_path.exists() else "fail",
            report_path=report_path if report_path.exists() else None,
            error=None if report_path.exists() else "Report file was not created. Agent may not have called submit_report.",
            duration_seconds=duration,
        )

    except Exception as exc:
        duration = (datetime.now() - start).total_seconds()
        return TaskResult(
            task_id=spec.id,
            title=spec.title,
            status="fail",
            error=str(exc),
            duration_seconds=duration,
        )


def _write_summary(result: OrchestratorResult, reports_dir: Path) -> Path:
    lines = [
        "# polyglot-eval Summary\n",
        f"**Repo:** {result.repo}  ",
        f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n",
        "| Task | Title | Status | Duration | Report |",
        "|------|-------|--------|----------|--------|",
    ]
    for tr in result.tasks_run:
        status_icon = "✅" if tr.status == "pass" else ("❌" if tr.status == "fail" else "⏭️")
        report_link = f"[{tr.report_path.name}]({tr.report_path})" if tr.report_path else "—"
        lines.append(
            f"| {tr.task_id} | {tr.title} | {status_icon} {tr.status} "
            f"| {tr.duration_seconds:.1f}s | {report_link} |"
        )

    if result.failed:
        lines.append("\n## Errors\n")
        for tr in result.failed:
            lines.append(f"### {tr.task_id} — {tr.title}\n```\n{tr.error}\n```\n")

    summary_path = reports_dir / "SUMMARY.md"
    summary_path.write_text("\n".join(lines), encoding="utf-8")
    return summary_path


async def run_async(
    repo: Path,
    task_ids: list[str],
    out_dir: Path,
    autonomy: Autonomy = Autonomy.GATED,
    model: str | None = None,
) -> OrchestratorResult:
    """Async entry point. Resolves tasks, validates repo, runs each task."""
    if not repo.exists():
        raise FileNotFoundError(f"Repository path does not exist: {repo}")
    if not repo.is_dir():
        raise NotADirectoryError(f"Repository path is not a directory: {repo}")

    ordered_ids = _resolve_task_ids(task_ids)
    specs = [get_task(tid) for tid in ordered_ids]

    reports_dir = out_dir
    reports_dir.mkdir(parents=True, exist_ok=True)

    # Validate repo state for any write task
    write_specs = [s for s in specs if s.writes_repo]
    if write_specs and autonomy != Autonomy.DRYRUN:
        for spec in write_specs:
            try:
                branch = validate_repo_state(repo, spec.id)
                print(f"✓ Branch '{branch}' ready for {spec.id}.")
            except RuntimeError as exc:
                print(f"⚠️  Skipping {spec.id}: {exc}", file=sys.stderr)

    # Create MCP server
    try:
        from .tools.report_tools import create_report_mcp_server
        task_spec_map = {s.id: s for s in specs}
        mcp_server, _ = create_report_mcp_server(reports_dir, task_spec_map)
    except ImportError:
        mcp_server = None

    result = OrchestratorResult(repo=repo)

    # Read-only tasks can run concurrently; write tasks run sequentially
    readonly_specs = [s for s in specs if not s.writes_repo]
    write_specs_ordered = [s for s in specs if s.writes_repo]

    # Run read-only tasks concurrently
    if readonly_specs:
        resolved_models = [resolve_model(s.id, model) for s in readonly_specs]
        tasks = [
            _run_single_task(s, repo, reports_dir, autonomy, m, mcp_server)
            for s, m in zip(readonly_specs, resolved_models)
        ]
        ro_results = await asyncio.gather(*tasks)
        # Preserve registry order
        result.tasks_run.extend(ro_results)

    # Run write tasks sequentially
    for spec in write_specs_ordered:
        m = resolve_model(spec.id, model)
        tr = await _run_single_task(spec, repo, reports_dir, autonomy, m, mcp_server)
        result.tasks_run.append(tr)

    # Sort results by registry order
    order = list(TASK_REGISTRY.keys())
    result.tasks_run.sort(key=lambda tr: order.index(tr.task_id))

    # Write summary
    result.summary_path = _write_summary(result, reports_dir)

    # Print final summary
    print(f"\n{'='*60}")
    print(f"  SUMMARY — {len(result.passed)}/{len(result.tasks_run)} tasks passed")
    print(f"  Report directory: {reports_dir}")
    print(f"{'='*60}\n")
    for tr in result.tasks_run:
        icon = "✅" if tr.status == "pass" else "❌"
        print(f"  {icon} {tr.task_id}: {tr.title} ({tr.duration_seconds:.1f}s)")
    print()

    # Combined dashboard when multiple tasks ran (or full pipeline)
    if len(ordered_ids) >= 2:
        try:
            from .ui_launcher import serve_all_viewers

            print("Launching combined dashboard …")
            urls = serve_all_viewers(repo)
            print("\n🖥️  Viewers")
            for name, url in urls.items():
                print(f"  {name}: {url}")
            print()
        except Exception as exc:
            print(f"⚠️  Dashboard launch skipped: {exc}", file=sys.stderr)

    return result


def run(
    repo: Path,
    task_ids: list[str],
    out_dir: Path,
    autonomy: Autonomy = Autonomy.GATED,
    model: str | None = None,
) -> OrchestratorResult:
    """Synchronous wrapper around run_async."""
    return asyncio.run(run_async(repo, task_ids, out_dir, autonomy, model))
