"""Tests for dashboard_builder and repo-agnostic generate_all_data."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from polyglot_eval.dashboard_builder import build_dashboard_data, load_task_data, write_dashboard_js
from polyglot_eval.generate_all_data import generate_all
from polyglot_eval.repo_scanner import scan_entities, scan_flow_steps


def test_scan_entities_finds_task_store(fixture_repo: Path):
    entities = scan_entities(fixture_repo)
    names = {e["name"] for e in entities}
    assert "TaskStore" in names or "Task" in names


def test_scan_flow_steps_non_empty(fixture_repo: Path):
    steps = scan_flow_steps(fixture_repo)
    assert len(steps) >= 1
    assert steps[0]["index"] == 1


def test_generate_all_creates_artifacts(fixture_repo: Path, tmp_path: Path):
    import shutil
    work = tmp_path / "work"
    shutil.copytree(fixture_repo, work)
    out = generate_all(work)
    assert len(out) == 6
    for tid in ("I1", "I2", "I3", "I4", "I5", "I6"):
        data = json.loads(out[tid].read_text(encoding="utf-8"))
        assert data["repoName"] == work.name
        assert "kyc" not in json.dumps(data).lower() or "kyc" in work.name.lower()


def test_build_dashboard_data_from_generated(fixture_repo: Path, tmp_path: Path):
    import shutil
    work = tmp_path / "work"
    shutil.copytree(fixture_repo, work)
    generate_all(work)
    dash = build_dashboard_data(work)
    assert dash["stats"]["total"] == 6
    assert dash["i1"] is not None
    assert dash["repoName"] == work.name


def test_load_task_data_missing_returns_none(tmp_path: Path):
    assert load_task_data(tmp_path, "I1") is None


def test_write_dashboard_js(tmp_path: Path):
    (tmp_path / "reports" / "artifacts" / "I1").mkdir(parents=True)
    (tmp_path / "reports" / "artifacts" / "I1" / "data.json").write_text(
        json.dumps({"repoName": "x", "status": "pass", "entities": [], "relationships": []}),
        encoding="utf-8",
    )
    dest = tmp_path / "out" / "data.js"
    data = write_dashboard_js(tmp_path, dest)
    assert dest.is_file()
    assert "dashboardData" in dest.read_text(encoding="utf-8")
    assert data["repoName"] == "x"
