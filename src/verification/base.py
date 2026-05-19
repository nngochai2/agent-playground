from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class VerificationResult:
    passed: bool
    output: str


class Verifier(ABC):
    @abstractmethod
    def run(self, working_dir: str) -> VerificationResult:
        """Run verification. Return pass/fail + output."""
        ...
