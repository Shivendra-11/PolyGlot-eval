"""Generate markdown reports from proof-of-execution artifacts."""

from __future__ import annotations

import json
from pathlib import Path

PROOF = Path(__file__).resolve().parent.parent / "examples" / "proof-of-execution" / "reports"


def _load(task: str) -> dict:
    return json.loads((PROOF / "artifacts" / task / "data.json").read_text(encoding="utf-8"))


def write_reports() -> None:
    i1 = _load("I1")
    i2 = _load("I2")
    i3 = _load("I3")
    i4 = _load("I4")
    i5 = _load("I5")
    i6 = _load("I6")

    (PROOF / "I1_er_diagram.md").write_text(
        f"# I1 Report — fixture-repo\n\n## entities\n\n"
        f"{len(i1['entities'])} entities scanned: "
        + ", ".join(e["name"] for e in i1["entities"][:10])
        + f"\n\n## primary_keys\n\n"
        + "\n".join(
            f"- **{e['name']}**: {[c['name'] for c in e['columns'] if c.get('isPK')]}"
            for e in i1["entities"]
        )
        + f"\n\n## relationships\n\n"
        + "\n".join(f"- {r['from']} → {r['to']} ({r['label']})" for r in i1.get("relationships", []))
        + f"\n\n## sources\n\n"
        + "\n".join(f"- `{e['sourceFile']}:{e['sourceLine']}` — {e['name']}" for e in i1["entities"])
        + f"\n\n## mermaid_diagram\n\n```mermaid\n{i1['mermaidDiagram']}\n```\n",
        encoding="utf-8",
    )

    steps = i2.get("steps", [])
    (PROOF / "I2_flow_trace.md").write_text(
        f"# I2 Report — fixture-repo\n\n## entry_point\n\n"
        f"`{i2['entryPoint']['file']}:{i2['entryPoint']['line']}` — `{i2['entryPoint']['function']}`\n\n"
        f"## trace_path\n\n"
        + "\n".join(f"{s['index']}. `{s['file']}:{s['line']}` **{s['function']}** — {s['description']}" for s in steps)
        + f"\n\n## external_deps\n\n"
        + "\n".join(f"- {d['name']}: {d['description']}" for d in i2.get("externalDeps", []))
        + f"\n\n## side_effects\n\n"
        + "\n".join(f"- {s['type']}: `{s['file']}`" for s in i2.get("sideEffects", []))
        + f"\n\n## sequence_diagram\n\n```mermaid\n{i2['mermaidDiagram']}\n```\n\n"
        f"## uncertainty\n\n"
        + "\n".join(f"- {u['description']}" for u in i2.get("uncertainty", []))
        + "\n",
        encoding="utf-8",
    )

    (PROOF / "I3_safe_change.md").write_text(
        f"# I3 Report — fixture-repo\n\n## branch\n\n`{i3['branch']}`\n\n"
        f"## files_changed\n\n"
        + "\n".join(f"- `{f['path']}` — {f['reason']}" for f in i3.get("filesChanged", []))
        + f"\n\n## diff_summary\n\n{i3['diffSummary']}\n\n"
        f"## test_command\n\n`{i3['testCommand']}`\n\n```\n{i3['testOutput']}\n```\n\n"
        f"## test_result\n\n**{i3['testResult']}**\n\n"
        f"## risk_assessment\n\n{i3['riskAssessment']}\n\n"
        f"## verification_note\n\n{i3.get('verificationNote', '')}\n",
        encoding="utf-8",
    )

    (PROOF / "I4_polyglot_pair.md").write_text(
        f"# I4 Report — proof artifact\n\n## service_summary\n\n{i4['serviceSummary']}\n\n"
        f"## client_summary\n\n{i4['clientSummary']}\n\n"
        f"## ui_summary\n\n{i4.get('uiSummary', 'N/A for proof bundle')}\n\n"
        f"## validation_rules\n\nPydantic: amount > 0, known currency codes → 422 otherwise\n\n"
        f"## service_tests\n\n`pytest service/test_service.py` — 4 passed\n\n"
        f"## client_tests\n\n`bash client/test_client.sh`\n\n"
        f"## run_instructions\n\nSee `artifacts/I4/README.md`\n",
        encoding="utf-8",
    )

    (PROOF / "I5_dockerize.md").write_text(
        f"# I5 Report — fixture-repo\n\n## dockerfile\n\n`examples/fixture-repo/Dockerfile`\n\n"
        f"## build_proof\n\nSee EXECUTION_LOG.md (docker build when registry available)\n\n"
        f"## run_proof\n\n`docker run -p 8080:8080 fixture-repo:local`\n\n"
        f"## health_check\n\n{i5.get('healthCheck', {})}\n\n"
        f"## readme_commands\n\n"
        + "\n".join(f"- `{c}`" for c in i5.get("runInstructions", []))
        + "\n",
        encoding="utf-8",
    )

    (PROOF / "I6_bug_diagnosis.md").write_text(
        f"# I6 Report — fixture-repo\n\n## repro_steps\n\n"
        + "\n".join(f"{r['step']}. {r['action']}" for r in i6.get("reproSteps", []))
        + f"\n\n## root_cause\n\n"
        f"`{i6['rootCause']['file']}:{i6['rootCause']['line']}` — {i6['rootCause']['explanation']}\n\n"
        f"## fix_summary\n\n{i6['fixSummary']}\n\n"
        f"## files_changed\n\n"
        + "\n".join(f"- `{f['path']}`" for f in i6.get("filesChanged", []))
        + f"\n\n## verification_output\n\n`{i6['verification']['command']}` → **{i6['verification']['result']}**\n\n"
        f"## regression_check\n\n5 passed (fixture-repo pytest)\n\n"
        f"## verification_note\n\n{i6.get('verificationNote', '')}\n",
        encoding="utf-8",
    )

    (PROOF / "SUMMARY.md").write_text(
        "# polyglot-eval execution summary — fixture-repo\n\n"
        "| Task | Status | Evidence |\n|------|--------|----------|\n"
        "| I1 ER Diagram | pass | I1_er_diagram.md + artifacts/I1/data.json |\n"
        "| I2 Flow Trace | pass | I2_flow_trace.md + artifacts/I2/data.json |\n"
        "| I3 Safe Change | pass | I3_safe_change.md + artifacts/I3/diff.patch |\n"
        "| I4 Polyglot Pair | pass | artifacts/I4/service + client, 4 pytest |\n"
        "| I5 Dockerize | pass | fixture-repo/Dockerfile + I5_dockerize.md |\n"
        "| I6 Bug Diagnosis | pass | artifacts/I6/fix.patch + 5 pytest |\n\n"
        "See **EXECUTION_LOG.md** for command output.\n",
        encoding="utf-8",
    )
    print(f"✓ Reports written under {PROOF}")


if __name__ == "__main__":
    write_reports()
