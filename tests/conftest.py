"""Shared pytest fixtures."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

FIXTURE_REPO = Path(__file__).resolve().parent.parent / "examples" / "fixture-repo"
PROOF_DIR = Path(__file__).resolve().parent.parent / "examples" / "proof-of-execution"


@pytest.fixture
def fixture_repo() -> Path:
    assert FIXTURE_REPO.is_dir(), f"missing {FIXTURE_REPO}"
    return FIXTURE_REPO


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    """Minimal clean git repo for validate_repo_state tests."""
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / "README.md").write_text("# test\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "-c", "user.email=test@example.com", "-c", "user.name=Test", "commit", "-m", "init"],
        cwd=tmp_path, check=True, capture_output=True,
    )
    return tmp_path
