"""I3 — Safe Change

Gated-write task. Makes a minimal, safe, well-tested code change in the target repo on a
dedicated branch. Requires operator approval before any write.
"""

from .base import Deliverable, TaskSpec
from .i3_defaults import DEFAULT_I3_CHANGE

_SYSTEM_PROMPT = """\
You are a meticulous senior engineer performing a gated, minimal code change in an unfamiliar
repository. Every write operation requires operator approval before it executes.

## Your goal
Implement the change described in the kickoff message as safely and minimally as possible:
- Work on a dedicated branch (`polyglot-eval/I3`).
- Change only the files that are strictly necessary.
- Add or adjust at least one test that covers the change.
- Run the test suite and include the command + full output in the report.
- Never commit or push.

## Rules — follow them strictly
1. **Plan before writing.** Read and understand all relevant code before making any edit.
2. **Minimal diff.** Do not refactor or fix unrelated issues. Only touch what is needed.
3. **One branch, no commits.** The orchestrator has already created the branch for you. You may
   use `git diff HEAD` and `git status` to inspect your changes, but NEVER run `git commit`,
   `git push`, `git merge`, `git rebase`, or any command that alters git history.
4. **Run tests.** After editing, run the repo's test suite (or the narrowest relevant subset).
   Include the exact command you ran and the complete output in the report.
5. **Cite every changed file.** For each file you modify or create, explain why it had to change.
6. **Save a diff artifact.** Use `mcp__report__save_artifact` to save the output of `git diff HEAD`
   as `diff.patch`.
7. **Write dashboard data.** Save `reports/artifacts/I3/data.json` via `mcp__report__save_artifact`:
   ```json
   {{
     "repoName": "<repo>",
     "generatedAt": "<ISO>",
     "status": "pass",
     "branch": "polyglot-eval/I3",
     "changeTitle": "<short title>",
     "changeDescription": "<what changed>",
     "changeMotivation": "<why>",
     "changePlan": [{{ "step": 1, "action": "..." }}],
     "filesChanged": [{{ "path": "...", "reason": "...", "linesChanged": 4, "changeType": "modify", "snippet": "..." }}],
     "diffSummary": "<human summary>",
     "diffStats": {{ "filesTouched": 2, "linesAdded": 10, "linesRemoved": 0 }},
     "diffPreview": "<first 80 lines of git diff>",
     "tests": [{{ "name": "...", "status": "PASS", "durationMs": 42 }}],
     "testCommand": "pytest ...",
     "testOutput": "<full output>",
     "testResult": "PASS|FAIL",
     "lintResult": "PASS|FAIL",
     "riskAssessment": "<risks>",
     "rollbackSteps": ["git checkout -- path"],
     "relatedFiles": ["..."]
   }}
   ```
8. **Finish by calling** `mcp__report__submit_report` with all required sections.

## Change strategy
- Read the kickoff for the description of the desired change.
- Grep for the relevant code. Read the surrounding context.
- Identify the minimal set of lines to change.
- Read existing tests to understand the test patterns, then add/adjust a test.
- Run tests. If they fail, fix them (only within the scope of this task) and re-run.

## Deliverable contract
{contract}
"""

_KICKOFF = """\
Please implement the following change in this repository:

{change_description}

If no change is specified, analyse the repo and propose the single most valuable
small improvement (a bug fix, a missing validation, a performance tweak), describe it,
get operator approval via the gated permission system, then implement it.

Start by reading the relevant files, then plan the minimal diff, wait for approval on each
write, run tests, and submit the report.
"""

_DELIVERABLES = [
    Deliverable("branch", "The branch name used and the git command used to create it"),
    Deliverable(
        "files_changed",
        "Each file modified/created: its path, a one-sentence reason it had to change, "
        "and the key lines changed",
    ),
    Deliverable(
        "diff_summary",
        "A human-readable summary of the diff (the raw diff is saved as an artifact)",
    ),
    Deliverable(
        "test_command",
        "The exact test command run (e.g. `pytest tests/test_foo.py -v`) and the full output",
    ),
    Deliverable(
        "test_result",
        "PASS or FAIL, with explanation if FAIL and what further action is needed",
    ),
    Deliverable(
        "risk_assessment",
        "Potential side effects of this change on other parts of the codebase",
    ),
    Deliverable(
        "verification_note",
        "Agent-suggested vs manually-verified — what a human reviewer should double-check",
    ),
]

SPEC = TaskSpec(
    id="I3",
    slug="safe_change",
    title="Safe Code Change",
    description="Make a minimal, gated, well-tested change in the repo on a dedicated branch.",
    system_prompt=_SYSTEM_PROMPT.format(
        contract="\n".join(f"- `{d.key}`: {d.label}" for d in _DELIVERABLES)
    ),
    kickoff=_KICKOFF.format(change_description=DEFAULT_I3_CHANGE),
    allowed_tools=["Read", "Grep", "Glob", "Edit", "Write", "Bash"],
    permission_mode="default",
    writes_repo=True,
    deliverables=_DELIVERABLES,
    requires_mermaid=False,
)
