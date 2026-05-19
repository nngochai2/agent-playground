import re
import subprocess
import sys
from pathlib import Path


def _slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def branch_name(issue_id: str, title: str | None) -> str:
    if title:
        return f"agent/{issue_id}-{_slugify(title)}"
    return f"agent/{issue_id}"


def _run(args: list[str], cwd: str) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True)


def create(repo_path: str, branch: str) -> str:
    """Create a git worktree for *branch* inside the repo and return the worktree path."""
    worktree_path = str(Path(repo_path) / ".adlc-worktrees" / branch.replace("/", "-"))

    # Fail loudly if the branch already exists rather than overwriting it.
    result = _run(["git", "branch", "--list", branch], cwd=repo_path)
    if result.returncode != 0:
        sys.exit(
            f"ERROR: Could not list git branches in {repo_path}: {result.stderr.strip()}"
        )
    if result.stdout.strip():
        sys.exit(
            f"ERROR: Branch '{branch}' already exists in {repo_path}. "
            f"Delete it manually before re-running."
        )

    result = _run(
        ["git", "worktree", "add", "-b", branch, worktree_path],
        cwd=repo_path,
    )
    if result.returncode != 0:
        sys.exit(
            f"ERROR: Failed to create worktree at {worktree_path}: {result.stderr.strip()}"
        )

    return worktree_path


def remove(repo_path: str, worktree_path: str, branch: str) -> None:
    """Remove the worktree and delete the branch. Best-effort — logs but does not raise."""
    result = _run(["git", "worktree", "remove", "--force", worktree_path], cwd=repo_path)
    if result.returncode != 0:
        print(f"WARNING: Could not remove worktree {worktree_path}: {result.stderr.strip()}")

    result = _run(["git", "branch", "-d", branch], cwd=repo_path)
    if result.returncode != 0:
        print(f"WARNING: Could not delete branch {branch}: {result.stderr.strip()}")
