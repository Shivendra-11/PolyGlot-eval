"""Tests for I3/I6 self-contained kickoff defaults."""

from __future__ import annotations

from polyglot_eval.tasks.i3_defaults import DEFAULT_I3_CHANGE
from polyglot_eval.tasks.i3_safe_change import SPEC as I3_SPEC
from polyglot_eval.tasks.i6_defaults import DEFAULT_I6_BUG
from polyglot_eval.tasks.i6_bug_diagnosis import SPEC as I6_SPEC


def test_i3_kickoff_is_self_contained():
    assert "[describe" not in I3_SPEC.kickoff
    assert "validation" in I3_SPEC.kickoff.lower()
    assert DEFAULT_I3_CHANGE in I3_SPEC.kickoff or "validation" in DEFAULT_I3_CHANGE


def test_i6_kickoff_is_self_contained():
    assert "[describe" not in I6_SPEC.kickoff
    assert "edge-case" in I6_SPEC.kickoff.lower() or "edge-case" in DEFAULT_I6_BUG.lower()
