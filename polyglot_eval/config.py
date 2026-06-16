"""Global configuration: default model, autonomy modes, per-task model overrides."""

from __future__ import annotations

from enum import Enum

# Default model for every subagent unless overridden per task. Opus 4.8 is the most
# capable model and the right default for unfamiliar-repo reasoning and code edits.
DEFAULT_MODEL = "claude-opus-4-8"

# Per-task model overrides. Read-only diagram/trace tasks are well served by a
# cheaper model; keep the write/reasoning-heavy tasks on the default. Override any
# of these from the CLI with --model, which wins for every task.
TASK_MODEL_OVERRIDES: dict[str, str] = {
    # "I1": "claude-sonnet-4-6",
    # "I2": "claude-sonnet-4-6",
}


class Autonomy(str, Enum):
    """How freely a task may modify the target repo.

    GATED   - read-only tasks run freely; writes/bash that change state require
              operator approval (the default; safest in an unfamiliar repo).
    AUTO    - writes run without prompting, but genuinely destructive commands
              (rm -rf, git push, ...) are still hard-denied.
    DRYRUN  - no writes to the repo at all; the agent emits diffs into the report.
    """

    GATED = "gated"
    AUTO = "auto"
    DRYRUN = "dryrun"


def resolve_model(task_id: str, cli_model: str | None) -> str:
    """Pick the model for a task: CLI override > per-task override > default."""
    if cli_model:
        return cli_model
    return TASK_MODEL_OVERRIDES.get(task_id, DEFAULT_MODEL)
