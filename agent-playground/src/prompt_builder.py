import re
import sys
from pathlib import Path

_TEMPLATE_PATH = Path(__file__).parent.parent / "prompts" / "coding_prompt.md"
_PLACEHOLDER_RE = re.compile(r"\{\{[A-Z_]+\}\}")


def build(issue_id: str, branch_name: str, target_branch: str) -> str:
    if not _TEMPLATE_PATH.exists():
        sys.exit(f"ERROR: Prompt template not found at {_TEMPLATE_PATH}")

    template = _TEMPLATE_PATH.read_text(encoding="utf-8")

    prompt = (
        template
        .replace("{{ISSUE_ID}}", issue_id)
        .replace("{{BRANCH_NAME}}", branch_name)
        .replace("{{TARGET_BRANCH}}", target_branch)
    )

    remaining = _PLACEHOLDER_RE.findall(prompt)
    if remaining:
        sys.exit(
            f"ERROR: Prompt template has unsubstituted placeholders: {', '.join(remaining)}"
        )

    return prompt
