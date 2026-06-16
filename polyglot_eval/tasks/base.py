"""TaskSpec: the contract for one Intermediate eval task.

Each task is one specialized subagent. A TaskSpec carries everything the
orchestrator needs to build a `ClaudeAgentOptions` for it, plus the deliverable
contract that the `submit_report` tool validates against.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Fully-qualified names of the custom MCP report tools (server name "report").
# The SDK exposes SDK MCP tools as mcp__<server>__<tool>.
TOOL_SUBMIT_REPORT = "mcp__report__submit_report"
TOOL_SAVE_ARTIFACT = "mcp__report__save_artifact"
TOOL_CHECK_MERMAID = "mcp__report__check_mermaid"
REPORT_TOOLS = [TOOL_SUBMIT_REPORT, TOOL_SAVE_ARTIFACT, TOOL_CHECK_MERMAID]


@dataclass(frozen=True)
class Deliverable:
    """One required section of a task's report.

    `key` is the machine name the agent must use in the `sections` dict passed to
    submit_report; `label` is the human-readable "Show:" bullet from the eval.
    """

    key: str
    label: str


@dataclass(frozen=True)
class TaskSpec:
    id: str  # e.g. "I1"
    slug: str  # e.g. "er_diagram" -> report file I1_er_diagram.md
    title: str
    system_prompt: str
    kickoff: str  # the user-turn prompt that starts the task
    allowed_tools: list[str]  # built-in tool names only (report tools added by orchestrator)
    permission_mode: str  # "plan" for read-only tasks, "default" for write tasks
    writes_repo: bool
    deliverables: list[Deliverable]
    requires_mermaid: bool = False
    description: str = ""  # one-line, used for the AgentDefinition + .claude/agents mirror

    @property
    def report_filename(self) -> str:
        return f"{self.id}_{self.slug}.md"

    @property
    def required_section_keys(self) -> list[str]:
        return [d.key for d in self.deliverables]

    def effective_allowed_tools(self) -> list[str]:
        """Built-in tools plus the report tools every task may call."""
        return [*self.allowed_tools, *REPORT_TOOLS]

    def contract_text(self) -> str:
        """Human-readable deliverable checklist, injected into the system prompt."""
        lines = [f"- `{d.key}`: {d.label}" for d in self.deliverables]
        mer = (
            "\n- You MUST include at least one valid Mermaid diagram in `mermaid`."
            if self.requires_mermaid
            else ""
        )
        return "\n".join(lines) + mer

    def as_agent_definition(self):
        """Export as a Claude Agent SDK AgentDefinition (camelCase fields).

        Lets the same task double as a Claude Code subagent under .claude/agents/.
        Imported lazily so the registry can be inspected without the SDK installed.
        """
        from claude_agent_sdk import AgentDefinition

        return AgentDefinition(
            description=self.description or self.title,
            prompt=self.system_prompt,
            tools=self.effective_allowed_tools(),
            permissionMode=self.permission_mode,
        )
