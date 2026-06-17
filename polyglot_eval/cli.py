"""CLI entry point for polyglot-eval.

Usage:
    polyglot-eval --repo /path/to/repo --tasks I1,I3
    polyglot-eval --repo . --tasks all --autonomy auto
    polyglot-eval --repo . --tasks I1 --out ./my-reports
    polyglot-eval --list-tasks
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import Autonomy, DEFAULT_MODEL
from .tasks.registry import TASK_REGISTRY


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="polyglot-eval",
        description="Repo-agnostic AI agent that runs Intermediate eval tasks (I1–I6).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  polyglot-eval --repo . --tasks I1
  polyglot-eval --repo /path/to/repo --tasks I1,I2 --autonomy dryrun
  polyglot-eval --repo . --tasks all --model claude-sonnet-4-6
  polyglot-eval --list-tasks
        """,
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path("."),
        help="Path to the target repository (default: current directory).",
    )
    parser.add_argument(
        "--tasks",
        default="all",
        help=(
            "Comma-separated task IDs to run (e.g. I1,I3) or 'all'. "
            "Valid IDs: " + ", ".join(TASK_REGISTRY.keys())
        ),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output directory for reports (default: <repo>/reports/).",
    )
    parser.add_argument(
        "--autonomy",
        choices=[a.value for a in Autonomy],
        default=Autonomy.GATED.value,
        help=(
            "Write autonomy mode: "
            "gated (default, prompts for approval), "
            "auto (writes without prompting, hard-denies destructive commands), "
            "dryrun (no writes, emits diffs into report)."
        ),
    )
    parser.add_argument(
        "--model",
        default=None,
        help=f"Model to use for all tasks (default: {DEFAULT_MODEL}). Overrides per-task defaults.",
    )
    parser.add_argument(
        "--list-tasks",
        action="store_true",
        help="List all available tasks and exit.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    # Subcommand: polyglot-eval generate-data --repo PATH [--serve]
    if argv and argv[0] == "generate-data":
        from .generate_all_data import main as generate_main
        return generate_main(argv[1:])

    # Subcommand: polyglot-eval deploy-ui --repo PATH [--token TOKEN]
    if argv and argv[0] == "deploy-ui":
        from .vercel_deploy import main as deploy_ui_main
        return deploy_ui_main(argv[1:])

    # Subcommand: polyglot-eval serve-ui --task I1 --data path/to/data.js
    if argv and argv[0] == "serve-ui":
        from .ui_launcher import main as serve_ui_main
        return serve_ui_main(argv[1:])

    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.list_tasks:
        print("\nAvailable polyglot-eval tasks:\n")
        for tid, spec in TASK_REGISTRY.items():
            mode = "read-only" if not spec.writes_repo else "writes-repo"
            print(f"  {tid}  ({mode})  — {spec.title}")
            print(f"       {spec.description}")
        print()
        return 0

    repo = args.repo.resolve()
    if not repo.exists():
        print(f"ERROR: --repo '{repo}' does not exist.", file=sys.stderr)
        return 1

    task_ids = [t.strip().upper() for t in args.tasks.split(",") if t.strip()]
    if not task_ids:
        task_ids = ["all"]

    out_dir = args.out if args.out else repo / "reports"
    autonomy = Autonomy(args.autonomy)

    # Import here so the CLI is importable even without the SDK
    try:
        from .orchestrator import run
    except ImportError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    try:
        result = run(
            repo=repo,
            task_ids=task_ids,
            out_dir=out_dir,
            autonomy=autonomy,
            model=args.model,
        )
    except (FileNotFoundError, NotADirectoryError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 130

    return 0 if not result.failed else 1


if __name__ == "__main__":
    sys.exit(main())
