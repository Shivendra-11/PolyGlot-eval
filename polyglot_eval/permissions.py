"""Permission gating for write-capable tasks.

make_permission_handler(autonomy, repo) returns a can_use_tool callback that the
Claude Agent SDK accepts as ClaudeAgentOptions.can_use_tool. It enforces:

  GATED   — prompts the CLI operator for approval on every write/destructive bash.
  AUTO    — allows writes; hard-denies genuinely destructive patterns.
  DRYRUN  — denies all writes; agent should emit diffs into the report only.

Additionally, before any write task runs, validate_repo_state() checks that the
target directory is a git repo with a clean working tree and creates a task branch.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Callable

from .config import Autonomy

# ---------------------------------------------------------------------------
# Destructive pattern hard-denials (applied in ALL autonomy modes)
# ---------------------------------------------------------------------------

_HARD_DENY_PATTERNS: list[re.Pattern] = [
    re.compile(r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f\b"),   # rm -rf
    re.compile(r"\bgit\s+push\b"),                     # git push
    re.compile(r"\bgit\s+commit\b"),                   # git commit
    re.compile(r"\bgit\s+merge\b"),                    # git merge
    re.compile(r"\bgit\s+rebase\b"),                   # git rebase
    re.compile(r"\bdrop\s+table\b", re.IGNORECASE),    # DROP TABLE
    re.compile(r"\btruncate\s+table\b", re.IGNORECASE),
    re.compile(r"\bdocker\s+push\b"),                  # docker push
    re.compile(r"\bnpm\s+publish\b"),                  # npm publish
    re.compile(r"\bpip\s+publish\b"),
    re.compile(r"\btwine\s+upload\b"),
]

# UI component files that I1/I2 agents must NEVER write — they are pre-built.
# Only `data.js` is allowed to be created/modified in those tasks.
_UI_READONLY_FILES = {
    "App.jsx", "App.css", "main.jsx",
    "index.html", "package.json", "vite.config.js",
}
# Task IDs that have pre-built UIs the agent must not recreate.
_PREBUILT_UI_TASKS = {"I1", "I2"}
# Target-repo paths where UI scaffolding must never appear (data.js lives one level up).
_UI_ARTIFACT_SUBDIRS = ("artifacts/i1/ui", "artifacts/i2/ui")

# Bash sub-commands that are safe to allow without gating (read-only git/fs ops)
_SAFE_BASH_PATTERNS: list[re.Pattern] = [
    re.compile(r"^(ls|cat|head|tail|find|echo|pwd|which|git (status|diff|log|branch|show))"),
    re.compile(r"^git (status|diff|log|branch|show)"),
    re.compile(r"^(pytest|python -m pytest|npm test|cargo test|go test)"),
    re.compile(r"^(pip|pip3) (install|list|show|freeze)"),
    re.compile(r"^(docker (build|run|stop|rm|ps|images|logs))"),
    re.compile(r"^(curl|wget) "),
    re.compile(r"^mmdc "),
]

_WRITE_TOOLS = {"Edit", "Write"}
_BASH_TOOL = "Bash"


def _is_hard_denied(tool_name: str, tool_input: dict) -> bool:
    """Return True if the tool call must be denied in all autonomy modes."""
    if tool_name == _BASH_TOOL:
        cmd = tool_input.get("command", tool_input.get("input", ""))
        return any(p.search(cmd) for p in _HARD_DENY_PATTERNS)
    return False


def _is_prebuilt_ui_write(tool_name: str, tool_input: dict, task_id: str) -> bool:
    """Return True if the agent is trying to write a pre-built UI file it must not touch.

    For I1/I2 the React UI is served from the polyglot-eval install via ``serve-ui``.
    The agent may only write ``reports/artifacts/I1/data.js`` (or I2) plus the markdown report.
    """
    if task_id not in _PREBUILT_UI_TASKS:
        return False

    path = tool_input.get("file_path", tool_input.get("path", ""))
    norm = path.replace("\\", "/").lower() if path else ""

    if tool_name in _WRITE_TOOLS:
        basename = Path(path).name if path else ""
        if basename in _UI_READONLY_FILES:
            return True
        if any(sub in norm for sub in _UI_ARTIFACT_SUBDIRS):
            return True
        # Legacy path — data.js must not live under ui/
        if basename == "data.js" and "/ui/" in norm:
            return True

    if tool_name == _BASH_TOOL:
        cmd = tool_input.get("command", tool_input.get("input", ""))
        cmd_lower = cmd.lower()
        for fname in _UI_READONLY_FILES:
            if fname.lower() in cmd_lower and (">>" in cmd or ">" in cmd or "tee" in cmd):
                return True
        if any(sub in cmd_lower for sub in _UI_ARTIFACT_SUBDIRS):
            return True
        if "npm install" in cmd_lower and "/ui" in cmd_lower and "artifacts/i" in cmd_lower:
            return True
        if "npm run dev" in cmd_lower and "artifacts/i" in cmd_lower:
            return True
    return False


def _is_safe_bash(tool_input: dict) -> bool:
    """Return True if a Bash command is read-only and safe to auto-approve."""
    cmd = (tool_input.get("command", tool_input.get("input", ""))).strip()
    return any(p.match(cmd) for p in _SAFE_BASH_PATTERNS)


def _prompt_operator(tool_name: str, tool_input: dict) -> bool:
    """Print a gated-approval prompt and wait for the operator's response."""
    print("\n" + "=" * 60)
    print(f"⚠️  GATED WRITE REQUEST — Tool: {tool_name}")
    if tool_name == _BASH_TOOL:
        cmd = tool_input.get("command", tool_input.get("input", ""))
        print(f"   Command: {cmd}")
    else:
        path = tool_input.get("file_path", tool_input.get("path", "<unknown>"))
        print(f"   File: {path}")
    print("=" * 60)
    answer = input("Allow this operation? [y/N] ").strip().lower()
    return answer in {"y", "yes"}


def make_permission_handler(autonomy: Autonomy, repo: Path, task_id: str = "") -> Callable:
    """Return a can_use_tool callback for the given autonomy mode.

    The callback signature matches what Claude Agent SDK expects:
        can_use_tool(tool_name: str, tool_input: dict) -> PermissionResult
    """
    try:
        from claude_agent_sdk import PermissionResultAllow, PermissionResultDeny
    except ImportError:
        # If SDK not installed, return a simple stub (useful for tests).
        def _stub(tool_name: str, tool_input: dict):
            return True
        return _stub

    def _handler(tool_name: str, tool_input: dict):
        # Hard deny — all modes
        if _is_hard_denied(tool_name, tool_input):
            cmd = tool_input.get("command", tool_input.get("input", ""))
            return PermissionResultDeny(
                reason=f"Hard-denied: '{cmd}' matches a destructive pattern "
                       f"(git push, git commit, rm -rf, docker push, etc.) "
                       f"that polyglot-eval never allows."
            )

        # Pre-built UI guard — I1 and I2 only
        if _is_prebuilt_ui_write(tool_name, tool_input, task_id):
            path = tool_input.get("file_path", tool_input.get("path", ""))
            basename = Path(path).name if path else tool_input.get("command", "")
            return PermissionResultDeny(
                reason=(
                    f"Pre-built UI guard: You tried to write or scaffold UI files for task {task_id}. "
                    f"The React UI is served from the polyglot-eval install — do NOT copy or generate "
                    f"App.jsx, package.json, or anything under reports/artifacts/{task_id}/ui/. "
                    f"Write ONLY reports/artifacts/{task_id}/data.js, then run: "
                    f"polyglot-eval serve-ui --task {task_id} --data reports/artifacts/{task_id}/data.js"
                )
            )

        if autonomy == Autonomy.DRYRUN:
            if tool_name in _WRITE_TOOLS or tool_name == _BASH_TOOL:
                return PermissionResultDeny(
                    reason="DRYRUN mode: all writes and shell commands are blocked. "
                           "Emit the intended changes as diffs in the report instead."
                )
            return PermissionResultAllow()

        if autonomy == Autonomy.AUTO:
            return PermissionResultAllow()

        # GATED mode (default)
        if tool_name in _WRITE_TOOLS:
            if _prompt_operator(tool_name, tool_input):
                return PermissionResultAllow()
            return PermissionResultDeny(reason="Operator declined the write operation.")

        if tool_name == _BASH_TOOL:
            if _is_safe_bash(tool_input):
                return PermissionResultAllow()
            if _prompt_operator(tool_name, tool_input):
                return PermissionResultAllow()
            return PermissionResultDeny(reason="Operator declined the bash command.")

        # All other tools (Read, Grep, Glob, MCP tools) — allow freely
        return PermissionResultAllow()

    return _handler


# ---------------------------------------------------------------------------
# Pre-flight repo validation for write tasks
# ---------------------------------------------------------------------------


def validate_repo_state(repo: Path, task_id: str) -> str:
    """Check git cleanliness and create/checkout a task branch.

    Returns the branch name on success. Raises RuntimeError if the repo is
    not safe to write to (not a git repo, dirty tree, etc.).
    """
    # Is it a git repo?
    result = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=repo, capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"'{repo}' is not inside a git repository. "
            "polyglot-eval write tasks require a git repo so changes can be tracked on a branch."
        )

    # Is the working tree clean?
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo, capture_output=True, text=True
    )
    if status.stdout.strip():
        raise RuntimeError(
            f"Working tree at '{repo}' has uncommitted changes:\n{status.stdout}\n"
            "Please commit or stash your changes before running a write task."
        )

    # Create / checkout the task branch
    branch = f"polyglot-eval/{task_id.lower()}"
    checkout = subprocess.run(
        ["git", "checkout", "-B", branch],
        cwd=repo, capture_output=True, text=True
    )
    if checkout.returncode != 0:
        raise RuntimeError(
            f"Failed to create branch '{branch}': {checkout.stderr.strip()}"
        )

    return branch
