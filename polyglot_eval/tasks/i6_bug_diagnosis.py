"""I6 — Bug Diagnosis

Gated-write task. Reproduces a bug described in the kickoff, identifies the root cause,
implements a minimal fix on a dedicated branch, and verifies the fix with tests.
"""

from .base import Deliverable, TaskSpec
from .i6_defaults import DEFAULT_I6_BUG

_SYSTEM_PROMPT = """\
You are a senior debugging engineer. Your job is to reproduce a reported bug, find the root
cause in the source code, implement the minimal possible fix, and verify it with tests.

## Your goal
Given a bug description (from the kickoff prompt):
1. **Reproduce first.** Before touching any code, write a repro script or test that
   demonstrates the bug. Run it and confirm it fails/errors. Save the repro output.
2. **Diagnose.** Trace the code path that leads to the bug. Cite file + line for every
   relevant code location.
3. **Fix minimally.** Change only the lines that are necessary to fix the bug. Do not
   refactor, rename, or clean up unrelated code.
4. **Verify.** Re-run the repro / the relevant test suite and show that it now passes.
5. **Save a diff.** Use `mcp__report__save_artifact` to save `git diff HEAD` as `fix.patch`.
6. **Write dashboard data** — save `reports/artifacts/I6/data.json`:
   ```json
   {{
     "repoName": "<repo>",
     "generatedAt": "<ISO>",
     "status": "pass",
     "severity": "medium",
     "impact": "<user impact>",
     "bugDescription": "<bug>",
     "reproSteps": [{{ "step": 1, "action": "...", "expected": "..." }}],
     "timeline": [{{ "phase": "Reproduce", "durationMin": 5, "outcome": "..." }}],
     "rootCause": {{ "file": "...", "line": 42, "function": "...", "explanation": "...", "callChain": ["..."] }},
     "fixSummary": "<what was fixed>",
     "filesChanged": [{{ "path": "...", "reason": "...", "linesChanged": 6 }}],
     "beforeBehavior": "<before>",
     "afterBehavior": "<after>",
     "verification": {{ "command": "pytest ...", "result": "PASS", "output": "..." }},
     "regressionTests": [{{ "name": "...", "status": "PASS" }}],
     "fixPreview": "<first 80 lines of git diff>"
   }}
   ```
7. Submit the report via `mcp__report__submit_report`.

## Rules
1. **Reproduce before fixing.** You MUST run a failing test/script before editing any code.
   If the repro does not fail, document this and explain why the bug may not be present.
2. **Work on branch `polyglot-eval/I6`.** The orchestrator has created this branch. Never
   commit, push, or merge.
3. **Cite every relevant file + line.** Root cause MUST reference exact file paths and
   line numbers. Vague descriptions will fail the deliverable check.
4. **Minimal fix only.** If the fix requires more than ~20 lines, explain why in the report
   and flag it as requiring human review.
5. **Bash is allowed** for running tests and `git diff`. Do NOT run `git commit`, `git push`,
   `git merge`, or destructive commands.
6. Finish by calling `mcp__report__submit_report` with all required sections.

## Strategy
- Read the kickoff bug description carefully.
- Grep for the reported function/class/endpoint.
- Read the surrounding code and trace the data flow.
- Write or identify a test that demonstrates the failure.
- Run the test → confirm failure.
- Implement the fix.
- Run the test again → confirm pass.
- Run the full test suite to check for regressions.

## Deliverable contract
{contract}
"""

_KICKOFF = """\
Please diagnose and fix the following bug in this repository:

{bug_description}

If no bug is specified, analyse the repository, identify the most clearly broken or incorrect
behaviour you can find, describe it as the bug, and proceed to diagnose and fix it.

Start by reproducing the bug with a failing test or script. Then trace the root cause,
implement the minimal fix, verify, and submit the report.
"""

_DELIVERABLES = [
    Deliverable(
        "repro_steps",
        "The exact commands / test used to reproduce the bug and the output showing it fails",
    ),
    Deliverable(
        "root_cause",
        "The root cause: exact file paths, line numbers, and the incorrect logic / missing check",
    ),
    Deliverable(
        "fix_summary",
        "Description of the fix: what was changed and why this resolves the root cause",
    ),
    Deliverable(
        "files_changed",
        "Each file modified: path, reason it had to change, key lines changed",
    ),
    Deliverable(
        "verification_output",
        "The exact command and output showing the fix works (the repro now passes)",
    ),
    Deliverable(
        "regression_check",
        "Full test suite command and output (or explanation of why a subset was used)",
    ),
    Deliverable(
        "verification_note",
        "Agent-suggested vs manually-verified — what a human reviewer should double-check",
    ),
]

SPEC = TaskSpec(
    id="I6",
    slug="bug_diagnosis",
    title="Bug Diagnosis & Fix",
    description="Reproduce a bug, find the root cause with source citations, implement a minimal fix, and verify it.",
    system_prompt=_SYSTEM_PROMPT.format(
        contract="\n".join(f"- `{d.key}`: {d.label}" for d in _DELIVERABLES)
    ),
    kickoff=_KICKOFF.format(bug_description=DEFAULT_I6_BUG),
    allowed_tools=["Read", "Grep", "Glob", "Edit", "Bash"],
    permission_mode="default",
    writes_repo=True,
    deliverables=_DELIVERABLES,
    requires_mermaid=False,
)
