"""Tests for polyglot_eval.permissions."""

from __future__ import annotations

import pytest

from polyglot_eval.config import Autonomy
from polyglot_eval.permissions import (
    _is_hard_denied,
    _is_prebuilt_ui_write,
    _is_safe_bash,
    make_permission_handler,
    validate_repo_state,
)


@pytest.mark.parametrize(
    "cmd",
    [
        "rm -rf /tmp/x",
        "git push origin main",
        "git commit -m x",
        "docker push myimage",
        "DROP TABLE users",
    ],
)
def test_hard_deny_destructive_bash(cmd: str):
    assert _is_hard_denied("Bash", {"command": cmd})


def test_hard_deny_allows_readonly_bash():
    assert not _is_hard_denied("Bash", {"command": "git status"})


def test_prebuilt_ui_blocks_app_jsx_for_i1():
    assert _is_prebuilt_ui_write(
        "Write",
        {"file_path": "reports/artifacts/I1/ui/src/App.jsx"},
        "I1",
    )


def test_prebuilt_ui_allows_data_json_path_for_i1():
    assert not _is_prebuilt_ui_write(
        "Write",
        {"file_path": "reports/artifacts/I1/data.json"},
        "I1",
    )


def test_prebuilt_ui_not_applied_to_i3():
    assert not _is_prebuilt_ui_write(
        "Write",
        {"file_path": "src/foo.py"},
        "I3",
    )


@pytest.mark.parametrize(
    "cmd",
    ["git status", "pytest -q", "git diff HEAD", "curl -f http://localhost:8080/health"],
)
def test_safe_bash(cmd: str):
    assert _is_safe_bash({"command": cmd})


def test_unsafe_bash_not_auto_safe():
    assert not _is_safe_bash({"command": "npm install && npm run build"})


def test_validate_repo_state_creates_branch(git_repo):
    branch = validate_repo_state(git_repo, "I3")
    assert branch == "polyglot-eval/i3"


def test_validate_repo_state_rejects_dirty_tree(git_repo):
    (git_repo / "dirty.txt").write_text("x", encoding="utf-8")
    with pytest.raises(RuntimeError, match="uncommitted"):
        validate_repo_state(git_repo, "I3")


def test_make_permission_handler_stub_without_sdk():
    from pathlib import Path
    handler = make_permission_handler(Autonomy.GATED, Path("."), "I1")
    assert callable(handler)
