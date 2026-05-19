from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class AgentResult:
    success: bool
    output: str
    exit_code: int


class AgentRunner(ABC):
    @abstractmethod
    def is_available(self) -> bool:
        """Return True if this agent's CLI is installed and accessible."""
        ...

    @abstractmethod
    def run(self, prompt: str, working_dir: str, timeout: int) -> AgentResult:
        """Invoke the agent with the assembled prompt in the given worktree directory."""
        ...
