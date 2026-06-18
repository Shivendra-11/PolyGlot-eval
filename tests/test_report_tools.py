"""Tests for Mermaid validation in report_tools."""

from __future__ import annotations

import pytest

from polyglot_eval.tools.report_tools import (
    _structural_lint,
    check_mermaid,
    save_artifact,
    submit_report,
)


def test_structural_lint_valid_er():
    diagram = "erDiagram\n    User {\n        string id\n    }"
    assert _structural_lint(diagram) == []


def test_structural_lint_invalid_header():
    errors = _structural_lint("not a diagram\n    foo")
    assert errors
    assert "header" in errors[0].lower() or "recognised" in errors[0].lower()


def test_structural_lint_unbalanced_braces():
    errors = _structural_lint("flowchart LR\n    A --> B {")
    assert any("brace" in e.lower() for e in errors)


def test_check_mermaid_ok():
    assert check_mermaid("sequenceDiagram\n    A->>B: hi").startswith("OK")


def test_check_mermaid_errors():
    result = check_mermaid("invalid diagram")
    assert result.startswith("ERRORS:")


def test_submit_report_missing_sections(tmp_path):
    with pytest.raises(ValueError, match="missing"):
        submit_report(
            "I1",
            sections={"branch": ""},
            mermaid=[],
            reports_dir=tmp_path,
            required_section_keys=["branch", "summary"],
            requires_mermaid=False,
        )


def test_submit_report_requires_mermaid(tmp_path):
    with pytest.raises(ValueError, match="Mermaid"):
        submit_report(
            "I1",
            sections={"branch": "ok", "summary": "ok"},
            mermaid=[],
            reports_dir=tmp_path,
            required_section_keys=["branch", "summary"],
            requires_mermaid=True,
        )


def test_submit_report_writes_file(tmp_path):
    msg = submit_report(
        "I1",
        sections={"branch": "main", "summary": "done"},
        mermaid=["erDiagram\n    A { string id }"],
        reports_dir=tmp_path,
        required_section_keys=["branch", "summary"],
        requires_mermaid=True,
    )
    assert "Report written" in msg
    assert (tmp_path / "I1.md").is_file()


def test_save_artifact(tmp_path):
    msg = save_artifact("I3", "diff.patch", "--- a\n+++ b", reports_dir=tmp_path)
    path = tmp_path / "artifacts" / "I3" / "diff.patch"
    assert path.is_file()
    assert "Artifact saved" in msg
