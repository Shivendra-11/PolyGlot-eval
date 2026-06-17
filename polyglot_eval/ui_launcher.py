"""Serve pre-built React UIs from the polyglot-eval install.

Individual tasks (I1, I2): copy ``data.json`` / ``data.js`` from the target repo into the
central UI tree and start Vite.

Dashboard: aggregate all I1–I6 artifacts from ``<repo>/reports/`` and serve on port 5175.
"""

from __future__ import annotations

import argparse
import json
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

from .dashboard_builder import TASK_META, write_dashboard_js, write_task_js_from_json

_PACKAGE_ROOT = Path(__file__).resolve().parent

_TASK_CONFIG = {
    "I1": {"ui_dir": _PACKAGE_ROOT / "ui" / "i1", "port": 5173, "label": "ER Diagram", "export": "erData"},
    "I2": {"ui_dir": _PACKAGE_ROOT / "ui" / "i2", "port": 5174, "label": "Flow Trace", "export": "traceData"},
    "DASHBOARD": {"ui_dir": _PACKAGE_ROOT / "ui" / "dashboard", "port": 5175, "label": "Dashboard", "export": "dashboardData"},
}


def _resolve_task(task: str) -> str:
    key = task.strip().upper()
    if key == "DASHBOARD":
        return key
    if key not in ("I1", "I2"):
        raise ValueError(f"Unknown task '{task}'. Valid: I1, I2, dashboard")
    return key


def _port_open(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex((host, port)) == 0


def _ensure_npm_deps(ui_dir: Path) -> None:
    if (ui_dir / "node_modules").exists():
        return
    print(f"Installing UI dependencies in {ui_dir} …", file=sys.stderr)
    subprocess.run(["npm", "install"], cwd=ui_dir, check=True)


def _stage_task_data(task_id: str, source: Path, ui_dir: Path) -> None:
    """Copy or convert task data into ``ui_dir/src/data.js``."""
    cfg = _TASK_CONFIG[task_id]
    dest = ui_dir / "src" / "data.js"
    dest.parent.mkdir(parents=True, exist_ok=True)
    source = source.resolve()

    if source.suffix == ".json":
        write_task_js_from_json(source, cfg["export"], dest)
        print(f"✓ Loaded {source} → {dest}", file=sys.stderr)
    elif source.resolve() != dest.resolve():
        shutil.copy2(source, dest)
        print(f"✓ Loaded {source} → {dest}", file=sys.stderr)
    else:
        print(f"✓ Using {dest}", file=sys.stderr)


def _start_vite(ui_dir: Path, port: int, label: str, host: str, open_browser: bool) -> dict:
    url = f"http://{host}:{port}/"
    _ensure_npm_deps(ui_dir)

    if _port_open(host, port):
        print(f"✓ {label} already running at {url}", file=sys.stderr)
        return {"url": url, "port": port, "reused": True}

    open_flag = "true" if open_browser else "false"
    proc = subprocess.Popen(
        ["npm", "run", "dev", "--", "--host", host, "--port", str(port), "--open", open_flag],
        cwd=ui_dir,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(30):
        if _port_open(host, port):
            print(f"✓ {label} running at {url}", file=sys.stderr)
            return {"url": url, "port": port, "pid": proc.pid, "reused": False}
        if proc.poll() is not None:
            raise RuntimeError(f"Vite exited unexpectedly (code {proc.returncode})")
        time.sleep(0.5)
    raise RuntimeError(f"Timed out waiting for {url}")


def serve_ui(
    task: str,
    *,
    data_path: Path | None = None,
    repo: Path | None = None,
    host: str = "127.0.0.1",
    open_browser: bool = False,
) -> dict:
    task_id = _resolve_task(task)
    cfg = _TASK_CONFIG[task_id]
    ui_dir = cfg["ui_dir"]

    if not ui_dir.is_dir():
        raise FileNotFoundError(f"Pre-built UI directory missing: {ui_dir}")

    if task_id == "DASHBOARD":
        if repo is None:
            raise ValueError("dashboard requires --repo pointing at the target repository")
        repo = repo.resolve()
        if not repo.is_dir():
            raise NotADirectoryError(f"Not a directory: {repo}")
        dest = ui_dir / "src" / "data.js"
        write_dashboard_js(repo, dest)
        print(f"✓ Built dashboard from {repo / 'reports'}", file=sys.stderr)
    else:
        if data_path is None:
            raise ValueError(f"{task_id} requires --data path to data.json or data.js")
        data_path = data_path.resolve()
        if not data_path.is_file():
            # Try default artifact path relative to repo if parent looks like a repo
            raise FileNotFoundError(f"Data file not found: {data_path}")
        _stage_task_data(task_id, data_path, ui_dir)

    result = _start_vite(ui_dir, cfg["port"], cfg["label"], host, open_browser)
    result["task"] = task_id
    return result


def serve_all_viewers(repo: Path, *, host: str = "127.0.0.1", open_browser: bool = False) -> dict[str, str]:
    """Start dashboard and any individual task viewers that have data artifacts."""
    repo = repo.resolve()
    urls: dict[str, str] = {}

    dash = serve_ui("dashboard", repo=repo, host=host, open_browser=open_browser)
    urls["dashboard"] = dash["url"]

    for task_id, meta in TASK_META.items():
        artifact_dir = repo / "reports" / "artifacts" / task_id
        json_path = artifact_dir / "data.json"
        js_path = artifact_dir / "data.js"
        source = json_path if json_path.is_file() else (js_path if js_path.is_file() else None)
        if source and task_id in ("I1", "I2"):
            try:
                r = serve_ui(task_id, data_path=source, host=host, open_browser=False)
                urls[task_id.lower()] = r["url"]
            except (FileNotFoundError, RuntimeError, ValueError) as exc:
                print(f"⚠ Skipped {task_id} viewer: {exc}", file=sys.stderr)

    return urls


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="polyglot-eval serve-ui",
        description="Serve I1/I2 viewers or the combined I1–I6 dashboard.",
    )
    parser.add_argument(
        "--task",
        required=True,
        choices=["I1", "I2", "i1", "i2", "dashboard", "all"],
        help="I1, I2, dashboard (combined), or all (dashboard + I1/I2 if data exists)",
    )
    parser.add_argument("--data", type=Path, default=None, help="Path to data.json or data.js (I1/I2)")
    parser.add_argument("--repo", type=Path, default=None, help="Target repo (required for dashboard/all)")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--open", action="store_true", help="Open browser tab")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    task = args.task.lower()

    try:
        if task == "all":
            if not args.repo:
                raise ValueError("--repo is required for --task all")
            urls = serve_all_viewers(args.repo, host=args.host, open_browser=args.open)
            print(json.dumps(urls, indent=2))
            return 0

        if task == "dashboard":
            result = serve_ui("dashboard", repo=args.repo, host=args.host, open_browser=args.open)
        else:
            result = serve_ui(task.upper(), data_path=args.data, host=args.host, open_browser=args.open)
    except (FileNotFoundError, ValueError, RuntimeError, NotADirectoryError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(result["url"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
