import sys
from datetime import datetime
from pathlib import Path

import click

from src import config as cfg_loader
from src import prompt_builder, worktree_manager
from src.agent.base import AgentRunner
from src.agent.claude_code import ClaudeCodeRunner
from src.agent.copilot_cli import CopilotCLIRunner
from src.verification.stub import StubVerifier


def _resolve_agent(override: str | None, cfg: dict) -> AgentRunner:
    preferred = override or cfg.get("agent", {}).get("preferred")

    candidates: list[AgentRunner]
    if preferred == "copilot":
        candidates = [CopilotCLIRunner()]
    elif preferred == "claude":
        candidates = [ClaudeCodeRunner()]
    else:
        candidates = [CopilotCLIRunner(), ClaudeCodeRunner()]

    for runner in candidates:
        if runner.is_available():
            if runner is not candidates[0] and preferred is None:
                print(f"WARNING: Copilot CLI not found. Falling back to Claude Code CLI.")
            return runner

    names = "Copilot CLI (`copilot`) or Claude Code CLI (`claude`)"
    sys.exit(f"ERROR: No agent CLI found. Install {names} and ensure it is on PATH.")


def _write_log(log_dir: str, issue_id: str, prompt: str, agent_output: str, verify_output: str) -> str:
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_file = log_path / f"{issue_id}-{timestamp}.log"
    log_file.write_text(
        f"=== PROMPT ===\n{prompt}\n\n"
        f"=== AGENT OUTPUT ===\n{agent_output}\n\n"
        f"=== VERIFICATION ===\n{verify_output}\n",
        encoding="utf-8",
    )
    return str(log_file)


@click.command()
@click.option("--issue", required=True, help="GitLab issue ID.")
@click.option(
    "--agent",
    "agent_override",
    type=click.Choice(["copilot", "claude"]),
    default=None,
    help="Force a specific agent. Defaults to auto-detection.",
)
@click.option("--title", default=None, help="Issue title used for branch naming.")
@click.option("--dry-run", is_flag=True, help="Print assembled prompt and exit.")
def main(issue: str, agent_override: str | None, title: str | None, dry_run: bool) -> None:
    cfg = cfg_loader.load()

    repo_path: str = cfg["git"]["repo_path"]
    target_branch: str = cfg["git"]["target_branch"]
    timeout: int = cfg["agent"]["timeout_seconds"]
    log_dir: str = cfg["logging"]["log_dir"]

    branch = worktree_manager.branch_name(issue, title)
    prompt = prompt_builder.build(issue, branch, target_branch)

    if dry_run:
        click.echo(prompt)
        sys.exit(0)

    runner = _resolve_agent(agent_override, cfg)
    verifier = StubVerifier()

    worktree_path = worktree_manager.create(repo_path, branch)
    try:
        print(f"Worktree created: {worktree_path}")
        print(f"Running agent ({type(runner).__name__})…")

        agent_result = runner.run(prompt, worktree_path, timeout)

        if not agent_result.success:
            print(f"\nERROR: Agent did not complete successfully (exit code {agent_result.exit_code}).")
            print("Check the run log for details.")
            _write_log(log_dir, issue, prompt, agent_result.output, "Agent failed — verification skipped.")
            sys.exit(1)

        verify_result = verifier.run(worktree_path)

        log_file = _write_log(log_dir, issue, prompt, agent_result.output, verify_result.output)
        print(f"Run log: {log_file}")

        if not verify_result.passed:
            print("ERROR: Verification failed. See run log.")
            sys.exit(1)

        print("Done. Review the MR opened by the agent, deploy to local WebSphere, and verify.")

    finally:
        worktree_manager.remove(repo_path, worktree_path, branch)


if __name__ == "__main__":
    main()
