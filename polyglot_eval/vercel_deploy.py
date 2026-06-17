"""Deploy polyglot-eval UIs to Vercel with fixed project names and URLs."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .dashboard_builder import write_dashboard_js, write_task_js_from_json
from .generate_all_data import generate_all

_PACKAGE_ROOT = Path(__file__).resolve().parent
_UI_ROOT = _PACKAGE_ROOT / "ui"
_DEFAULT_SCOPE = "shivendra-11s-projects"

# Fixed Vercel project names → https://<name>.vercel.app
VERCEL_PROJECTS = {
    "dashboard": "polyglot-eval",
    "i1": "polyglot-eval-i1",
    "i2": "polyglot-eval-i2",
}


def slugify_repo(repo: Path) -> str:
    """Filesystem repo folder name (stored in deploy manifest only)."""
    name = repo.resolve().name.lower()
    slug = re.sub(r"[^a-z0-9-]", "-", name)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug[:40] if slug else "repo"


def project_names() -> dict[str, str]:
    return dict(VERCEL_PROJECTS)


def expected_urls() -> dict[str, str]:
    return {key: f"https://{name}.vercel.app" for key, name in VERCEL_PROJECTS.items()}


def _run(cmd: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        cmd,
        cwd=cwd,
        env=merged,
        text=True,
        capture_output=True,
        check=False,
    )


def _ensure_build(ui_dir: Path) -> None:
    if not (ui_dir / "node_modules").is_dir():
        subprocess.run(["npm", "install"], cwd=ui_dir, check=True)
    subprocess.run(["npm", "run", "build"], cwd=ui_dir, check=True)


def _link_project(ui_dir: Path, project_name: str, *, token: str, scope: str) -> None:
    vercel_dir = ui_dir / ".vercel"
    if vercel_dir.is_dir():
        import shutil
        shutil.rmtree(vercel_dir)

    result = _run(
        [
            "npx", "vercel", "link",
            "--yes",
            "--project", project_name,
            "--scope", scope,
            "--token", token,
        ],
        cwd=ui_dir,
        env={"NODE_TLS_REJECT_UNAUTHORIZED": "0"},
    )
    if result.returncode != 0:
        raise RuntimeError(f"vercel link failed for {project_name}:\n{result.stderr or result.stdout}")


def _deploy_prod(ui_dir: Path, *, token: str, scope: str) -> str:
    result = _run(
        ["npx", "vercel", "--prod", "--yes", "--scope", scope, "--token", token],
        cwd=ui_dir,
        env={"NODE_TLS_REJECT_UNAUTHORIZED": "0"},
    )
    if result.returncode != 0:
        raise RuntimeError(f"vercel deploy failed:\n{result.stderr or result.stdout}")

    combined = (result.stdout or "") + (result.stderr or "")
    for line in combined.splitlines():
        if "Aliased" in line and "https://" in line:
            # ▲ Aliased         https://polyglot-dash-kyc-mini.vercel.app
            parts = line.split()
            for part in parts:
                if part.startswith("https://"):
                    return part.rstrip()
    for line in combined.splitlines():
        if "Production" in line and "https://" in line:
            parts = line.split()
            for part in parts:
                if part.startswith("https://") and "vercel.app" in part:
                    return part.rstrip()
    # Fallback: predictable alias from project link
    project_file = ui_dir / ".vercel" / "project.json"
    if project_file.is_file():
        data = json.loads(project_file.read_text(encoding="utf-8"))
        return f"https://{data['projectName']}.vercel.app"
    raise RuntimeError(f"Could not parse deploy URL:\n{combined}")


def stage_ui_data(repo: Path) -> dict[str, Path]:
    """Sync target-repo artifacts into I1/I2/dashboard source trees."""
    repo = repo.resolve()
    urls = expected_urls()

    i1_dest = _UI_ROOT / "i1" / "src" / "data.js"
    i2_dest = _UI_ROOT / "i2" / "src" / "data.js"
    dash_dest = _UI_ROOT / "dashboard" / "src" / "data.js"

    i1_json = repo / "reports" / "artifacts" / "I1" / "data.json"
    i2_json = repo / "reports" / "artifacts" / "I2" / "data.json"
    if not i1_json.is_file() or not i2_json.is_file():
        generate_all(repo)

    write_task_js_from_json(i1_json, "erData", i1_dest)
    write_task_js_from_json(i2_json, "traceData", i2_dest)
    write_dashboard_js(repo, dash_dest)

    env_prod = _UI_ROOT / "dashboard" / ".env.production"
    env_prod.write_text(
        f"VITE_I1_VIEWER_URL={urls['i1']}\n"
        f"VITE_I2_VIEWER_URL={urls['i2']}\n",
        encoding="utf-8",
    )
    return {"i1": i1_dest, "i2": i2_dest, "dashboard": dash_dest}


def deploy_repo_ui(
    repo: Path,
    *,
    token: str | None = None,
    scope: str = _DEFAULT_SCOPE,
    regenerate_data: bool = True,
    targets: list[str] | None = None,
) -> dict[str, Any]:
    """Deploy dashboard + I1 + I2 to fixed Vercel projects (same URLs every repo)."""
    repo = repo.resolve()
    if not repo.is_dir():
        raise NotADirectoryError(f"Not a directory: {repo}")

    token = token or os.environ.get("VERCEL_TOKEN")
    if not token:
        raise ValueError("Set VERCEL_TOKEN or pass --token")

    scope = os.environ.get("VERCEL_SCOPE", scope)
    slug = slugify_repo(repo)
    names = project_names()
    urls: dict[str, str] = {}

    if regenerate_data:
        generate_all(repo)
    stage_ui_data(repo)

    deploy_order = [
        ("i1", _UI_ROOT / "i1", names["i1"]),
        ("i2", _UI_ROOT / "i2", names["i2"]),
        ("dashboard", _UI_ROOT / "dashboard", names["dashboard"]),
    ]
    if targets:
        allowed = set(targets)
        deploy_order = [item for item in deploy_order if item[0] in allowed]

    for key, ui_dir, project_name in deploy_order:
        print(f"→ Building {key} ({project_name}) …", file=sys.stderr)
        _ensure_build(ui_dir)
        print(f"→ Linking + deploying {project_name} …", file=sys.stderr)
        _link_project(ui_dir, project_name, token=token, scope=scope)
        urls[key] = _deploy_prod(ui_dir, token=token, scope=scope)
        print(f"✓ {key}: {urls[key]}", file=sys.stderr)

    manifest = {
        "repoName": repo.name,
        "repoPath": str(repo),
        "repoSlug": slug,
        "deployedAt": datetime.now(timezone.utc).isoformat(),
        "vercelScope": scope,
        "projects": names,
        "urls": urls,
    }
    manifest_path = repo / "reports" / "polyglot-deploy.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"✓ Manifest → {manifest_path}", file=sys.stderr)
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Deploy polyglot-eval dashboard + I1 + I2 to Vercel (fixed URLs).",
    )
    parser.add_argument("--repo", type=Path, required=True, help="Target repository path")
    parser.add_argument("--token", default=None, help="Vercel token (default: VERCEL_TOKEN env)")
    parser.add_argument("--scope", default=_DEFAULT_SCOPE, help="Vercel team scope")
    parser.add_argument(
        "--skip-generate",
        action="store_true",
        help="Skip generate_all; use existing reports/artifacts data",
    )
    parser.add_argument(
        "--targets",
        default="all",
        help="Comma-separated: dashboard,i1,i2 or all (default: all)",
    )
    args = parser.parse_args(argv)

    targets = None
    if args.targets.strip().lower() != "all":
        targets = [t.strip().lower() for t in args.targets.split(",") if t.strip()]

    try:
        manifest = deploy_repo_ui(
            args.repo,
            token=args.token,
            scope=args.scope,
            regenerate_data=not args.skip_generate,
            targets=targets,
        )
    except (ValueError, RuntimeError, NotADirectoryError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
