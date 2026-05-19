import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

import click

from src import config as cfg_loader


@dataclass
class RunResult:
    issue_id: str
    success: bool
    exit_code: int
    output: str


def _run_one(issue_id: str, agent_override: str | None) -> RunResult:
    import subprocess

    cmd = [sys.executable, "orchestrator.py", "--issue", issue_id]
    if agent_override:
        cmd += ["--agent", agent_override]

    result = subprocess.run(cmd, capture_output=True, text=True)
    return RunResult(
        issue_id=issue_id,
        success=result.returncode == 0,
        exit_code=result.returncode,
        output=result.stdout + result.stderr,
    )


@click.command()
@click.option(
    "--issues",
    required=True,
    help="Comma-separated GitLab issue IDs to run in parallel.",
)
@click.option(
    "--agent",
    "agent_override",
    type=click.Choice(["copilot", "claude"]),
    default=None,
    help="Force a specific agent for all runs.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Print the commands that would run and exit.",
)
def main(issues: str, agent_override: str | None, dry_run: bool) -> None:
    issue_ids = [i.strip() for i in issues.split(",") if i.strip()]
    if not issue_ids:
        sys.exit("ERROR: --issues must contain at least one issue ID.")

    # Validate config exists and is well-formed before spawning anything.
    cfg_loader.load()

    if dry_run:
        for issue_id in issue_ids:
            cmd = [sys.executable, "orchestrator.py", "--issue", issue_id]
            if agent_override:
                cmd += ["--agent", agent_override]
            click.echo(" ".join(cmd))
        sys.exit(0)

    click.echo(
        f"Dispatching {len(issue_ids)} issue(s) in parallel: {', '.join(issue_ids)}\n"
    )

    results: list[RunResult] = []
    with ThreadPoolExecutor(max_workers=len(issue_ids)) as pool:
        futures = {
            pool.submit(_run_one, issue_id, agent_override): issue_id
            for issue_id in issue_ids
        }
        for future in as_completed(futures):
            result = future.result()
            status = "DONE  " if result.success else "FAILED"
            click.echo(f"  [{status}] issue {result.issue_id}")
            results.append(result)

    failed = [r for r in results if not r.success]

    if failed:
        click.echo("\n--- Output from failed runs ---")
        for r in failed:
            click.echo(f"\n=== Issue {r.issue_id} (exit {r.exit_code}) ===")
            click.echo(r.output.strip())

    click.echo(f"\n{'=' * 42}")
    click.echo(f"  {len(results) - len(failed)}/{len(results)} succeeded")
    for r in sorted(results, key=lambda x: x.issue_id):
        marker = "OK  " if r.success else "FAIL"
        click.echo(f"  [{marker}] issue {r.issue_id}")

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
