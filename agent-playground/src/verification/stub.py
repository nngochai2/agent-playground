from .base import VerificationResult, Verifier

_REMINDER = (
    "ACTION REQUIRED: Deploy the worktree branch to local WebSphere, "
    "walk the happy flow, and verify manually before merging the MR."
)


class StubVerifier(Verifier):
    def run(self, working_dir: str) -> VerificationResult:
        print(f"\n[verification] {_REMINDER}\n")
        return VerificationResult(passed=True, output=_REMINDER)
