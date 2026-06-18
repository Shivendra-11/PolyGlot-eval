"""Integration tests against proof-of-execution bundle."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PROOF = ROOT / "examples" / "proof-of-execution" / "reports"
FIXTURE = ROOT / "examples" / "fixture-repo"
I4_SERVICE = PROOF / "artifacts" / "I4" / "service"


def test_proof_artifacts_complete():
    for tid in ("I1", "I2", "I3", "I4", "I5", "I6"):
        path = PROOF / "artifacts" / tid / "data.json"
        assert path.is_file(), f"missing {path}"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data.get("status") in ("pass", "skipped")
        assert data.get("repoName") == "fixture-repo"


def test_proof_markdown_reports_exist():
    for name in (
        "SUMMARY.md", "EXECUTION_LOG.md",
        "I1_er_diagram.md", "I2_flow_trace.md", "I3_safe_change.md",
        "I4_polyglot_pair.md", "I5_dockerize.md", "I6_bug_diagnosis.md",
    ):
        assert (PROOF / name).is_file(), f"missing {name}"


def test_proof_patches_exist():
    assert (PROOF / "artifacts" / "I3" / "diff.patch").is_file()
    assert (PROOF / "artifacts" / "I6" / "fix.patch").is_file()


def test_i4_service_pytest():
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        cwd=I4_SERVICE,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "passed" in result.stdout.lower() or result.returncode == 0


def test_dashboard_builds_from_proof():
    from polyglot_eval.dashboard_builder import build_dashboard_data

    dash = build_dashboard_data(FIXTURE)
    assert dash["stats"]["passed"] >= 5
    assert dash["i1"] is not None
    assert dash["i6"] is not None


def test_submit_report_rejects_incomplete_i1(tmp_path):
    from polyglot_eval.tools.report_tools import submit_report

    with pytest.raises(ValueError, match="missing"):
        submit_report(
            "I1",
            sections={"entities": "only one section"},
            mermaid=[],
            reports_dir=tmp_path,
            required_section_keys=["entities", "primary_keys", "relationships"],
            requires_mermaid=True,
        )
