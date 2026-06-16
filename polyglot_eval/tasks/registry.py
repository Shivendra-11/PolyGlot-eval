"""TASK_REGISTRY — maps task ID → TaskSpec for all six Intermediate eval tasks.

Usage:
    from polyglot_eval.tasks.registry import TASK_REGISTRY, get_task, list_task_ids
"""

from __future__ import annotations

from .base import TaskSpec
from .i1_er_diagram import SPEC as I1
from .i2_flow_trace import SPEC as I2
from .i3_safe_change import SPEC as I3
from .i4_polyglot_pair import SPEC as I4
from .i5_dockerize import SPEC as I5
from .i6_bug_diagnosis import SPEC as I6

# Ordered dict preserving I1→I6 execution order.
TASK_REGISTRY: dict[str, TaskSpec] = {
    "I1": I1,
    "I2": I2,
    "I3": I3,
    "I4": I4,
    "I5": I5,
    "I6": I6,
}


def get_task(task_id: str) -> TaskSpec:
    """Return a TaskSpec by ID (e.g. "I1"). Raises KeyError on unknown IDs."""
    task_id = task_id.upper()
    if task_id not in TASK_REGISTRY:
        raise KeyError(
            f"Unknown task '{task_id}'. Valid tasks: {', '.join(TASK_REGISTRY)}"
        )
    return TASK_REGISTRY[task_id]


def list_task_ids() -> list[str]:
    """Return all task IDs in execution order."""
    return list(TASK_REGISTRY.keys())


def as_agent_definitions() -> dict[str, object]:
    """Export all tasks as Claude Agent SDK AgentDefinition objects.

    Used to generate the .claude/agents/ subagent files.
    """
    return {tid: spec.as_agent_definition() for tid, spec in TASK_REGISTRY.items()}
