import subprocess

from .base import AgentResult, AgentRunner

_COMPLETE_TOKEN = "<COMPLETE>"


class CopilotCLIRunner(AgentRunner):
    def is_available(self) -> bool:
        result = subprocess.run(
            ["copilot", "--version"], capture_output=True, text=True
        )
        return result.returncode == 0

    def run(self, prompt: str, working_dir: str, timeout: int) -> AgentResult:
        try:
            result = subprocess.run(
                ["copilot", "--prompt", prompt, "--allow-all-tools"],
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return AgentResult(success=False, output="Agent timed out.", exit_code=-1)

        output = result.stdout + result.stderr
        success = result.returncode == 0 and _COMPLETE_TOKEN in result.stdout
        return AgentResult(success=success, output=output, exit_code=result.returncode)
