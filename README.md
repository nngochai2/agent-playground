# ADLC Orchestrator — Claude Code Handover

## What this project is

A lightweight Python CLI tool that orchestrates an AI coding agent as part of an AI-assisted Development Loop (ADLC) on a legacy system.

The orchestrator's job is deliberately minimal — it does not integrate with GitLab, Neo4j, or any other service directly. Those are all available as MCP servers that the agent uses autonomously. The orchestrator only does what the agent cannot do for itself:

1. Creates a git worktree branch for the agent to work on
2. Builds a prompt instructing the agent what to do and which MCP servers to use
3. Invokes the AI coding agent with MCP servers configured
4. Runs a verification stub (pluggable for a future Docker/WebSphere loop)
5. Exits cleanly — the agent opens the MR itself via GitLab MCP

The developer then reviews the diff, deploys to local WebSphere, walks the happy flow, and merges if satisfied.

---

## Repository structure

```
adlc-orchestrator/
├── CLAUDE.md                  # This file
├── orchestrator.py            # CLI entry point — the only file the developer runs
├── config.yaml                # Environment config (see schema below)
├── config.yaml.example        # Committed placeholder — config.yaml is gitignored
├── requirements.txt
├── README.md
├── src/
│   ├── worktree_manager.py    # Git worktree create/cleanup
│   ├── prompt_builder.py      # Assembles prompt from template + issue ID
│   ├── agent/
│   │   ├── base.py            # Abstract AgentRunner interface
│   │   ├── copilot_cli.py     # Primary: GitHub Copilot CLI
│   │   └── claude_code.py     # Fallback: Claude Code CLI
│   └── verification/
│       ├── base.py            # Abstract Verifier interface
│       └── stub.py            # Always passes — reminds developer to verify manually
└── prompts/
    └── coding_prompt.md       # Prompt template with {{PLACEHOLDER}} substitution
```

---

## How the developer uses it

```bash
python orchestrator.py --issue 1234
```

Optional flags:
```bash
python orchestrator.py --issue 1234 --agent copilot           # force Copilot CLI
python orchestrator.py --issue 1234 --agent claude            # force Claude Code CLI
python orchestrator.py --issue 1234 --title "Fix VAT rounding" # include title in branch name
python orchestrator.py --issue 1234 --dry-run                 # print assembled prompt, do not invoke agent
```

`--title` is optional. Without it the branch is named `agent/<issue-id>`. With it: `agent/<issue-id>-<slugified-title>`. The orchestrator cannot fetch the title itself (no direct GitLab calls), so the developer supplies it when a descriptive branch name is wanted.

---

## MCP servers (agent's responsibility, not the orchestrator's)

The following are already available as MCP servers. The orchestrator does not call them. The agent uses them autonomously based on the prompt instructions.

| MCP Server | What the agent uses it for |
|------------|---------------------------|
| GitLab MCP | Fetch issue details, open MR |
| Document graph MCP | Query regulatory intent, business rules, architectural decisions |
| Code graph MCP | Query dependency map, blast radius, conventions |
| ADO MCP | Any Azure DevOps integration if needed |

The prompt template must instruct the agent to use these servers in the correct order before writing any code.

---

## Prompt template (prompts/coding_prompt.md)

This is the most important artefact in the project. The agent reads and acts on this.

The prompt instructs the agent to:
1. Fetch issue `{{ISSUE_ID}}` from GitLab MCP — get title, description, acceptance criteria
2. Load context — check the issue body for a preflight context block first; use it if present (KG nodes, shape constraints, in/out-of-scope components are already scoped). Only cold-query the document graph and code graph MCP if no preflight block is found.
3. Confirm scope boundaries explicitly before touching code — state which components will and will not be modified, and which KG regulatory nodes are in scope
4. Implement the change in the worktree directory, modifying only confirmed in-scope components
5. Open an MR via GitLab MCP from `{{BRANCH_NAME}}` targeting `{{TARGET_BRANCH}}`
6. Output `<COMPLETE>` when done

The orchestrator substitutes `{{ISSUE_ID}}`, `{{BRANCH_NAME}}`, and `{{TARGET_BRANCH}}` before passing the prompt to the agent. Everything else the agent resolves itself via MCP.

The orchestrator substitutes `{{ISSUE_ID}}`, `{{BRANCH_NAME}}`, and `{{TARGET_BRANCH}}` before passing the prompt to the agent. Everything else the agent resolves itself via MCP.

---

## Agent interface (pluggable)

```python
# src/agent/base.py
from abc import ABC, abstractmethod

class AgentRunner(ABC):
    @abstractmethod
    def is_available(self) -> bool:
        """Return True if this agent's CLI is installed and accessible."""
        ...

    @abstractmethod
    def run(self, prompt: str, working_dir: str) -> AgentResult:
        """Invoke the agent with the assembled prompt in the given worktree directory."""
        ...
```

**Auto-detection logic** (in `orchestrator.py`):
1. Try Copilot CLI — `is_available()` checks `copilot --version`. If True, use it.
2. If unavailable, try Claude Code CLI — `is_available()` checks `claude --version`. If True, use it and log a warning.
3. If neither available, exit with a clear message telling the developer what to install.

Note: the old `gh copilot` extension reached end-of-life October 2025 and is no longer used. The current standalone binary is `copilot`.

`--agent` flag overrides auto-detection.

---

## Verification interface (pluggable)

```python
# src/verification/base.py
from abc import ABC, abstractmethod

class Verifier(ABC):
    @abstractmethod
    def run(self, working_dir: str) -> VerificationResult:
        """Run verification. Return pass/fail + output."""
        ...
```

**v1 (`stub.py`):** Always returns pass. Logs a message reminding the developer to deploy to local WebSphere and walk the happy flow manually.

**Future:** A Docker-based implementation will build the EAR, deploy to containerised WebSphere, run Cucumber-JVM scenarios, and feed failures back to the agent loop. Deferred until WebSphere containerisation is proven viable.

---

## Git branching model

Four-layer model: `delivery → feature branch → remote branch → integration`

The orchestrator operates at the **feature branch** level:
- Creates a git worktree from the developer's current remote branch
- Worktree branch naming: `agent/<issue-id>` (default) or `agent/<issue-id>-<slugified-title>` when `--title` is supplied
- The agent opens the MR from the worktree branch targeting the developer's remote branch
- Developer handles the subsequent remote → integration MR manually

---

## config.yaml schema

```yaml
git:
  repo_path: /path/to/your/repo               # local repo root
  target_branch: origin/your-remote-branch    # MR target — developer's remote branch

agent:
  preferred: copilot                           # copilot | claude — overrides auto-detect
  timeout_seconds: 1200

verification:
  type: stub                                   # stub | docker (future)

logging:
  log_dir: .adlc-logs                          # run logs written here
```

No credentials. No service URLs. The agent handles all of that via its own MCP configuration.

---

## Build phases

Build in this order. Each phase must work before moving to the next.

### Phase 1 — Scaffold + config
- Directory structure as above
- `config.yaml` loading with validation (fail fast on missing required fields)
- `orchestrator.py` CLI skeleton with `--issue`, `--agent`, `--dry-run` flags
- `config.yaml.example` with placeholder values
- `README.md` with usage instructions
- `.gitignore` including `config.yaml` and `.adlc-logs/`

### Phase 2 — Worktree management
- `src/worktree_manager.py`: create worktree at `.adlc-worktrees/<branch-name>`
- Branch naming: `agent/<issue-id>-<slugified-title>` (slug: lowercase, hyphens, no special chars)
- Cleanup worktree on completion (success or failure) — always use try/finally
- Handle case where branch already exists: warn and exit, never overwrite

### Phase 3 — Prompt builder
- `src/prompt_builder.py`: load `prompts/coding_prompt.md`, substitute `{{ISSUE_ID}}`, `{{BRANCH_NAME}}`, `{{TARGET_BRANCH}}`
- `--dry-run`: print assembled prompt to stdout and exit
- Fail if any `{{PLACEHOLDER}}` remains unsubstituted after assembly

### Phase 4 — Agent runner
- `src/agent/base.py`: abstract interface + `AgentResult` dataclass
- `src/agent/copilot_cli.py`: `is_available()` via `copilot --version`, `run()` via subprocess
- `src/agent/claude_code.py`: `is_available()` via `claude --version`, `run()` via subprocess
- Auto-detection + `--agent` override in `orchestrator.py`

### Phase 5 — Verification stub
- `src/verification/base.py`: abstract interface + `VerificationResult` dataclass
- `src/verification/stub.py`: always passes, prints manual verification reminder

### Phase 6 — Wire together + logging
- Full happy path: worktree → prompt → agent → verify → exit
- Run log written to `.adlc-logs/<issue-id>-<timestamp>.log` (prompt, agent output, verification result)
- Error handling: fail fast, clear messages, worktree always cleaned up

---

## Error handling principles

- Fail fast and loudly — no silent failures
- Every error prints: what failed, why, and what the developer should do next
- Worktree is always cleaned up on failure (try/finally)
- Full run log always written to `.adlc-logs/` regardless of outcome

---

## Key constraints

- **Python only** — no Node, no TypeScript
- **No direct service integrations** — no GitLab API calls, no Neo4j driver, no HTTP clients. The agent handles all of that via MCP.
- **No Docker in v1** — verification is a stub
- **Self-hosted GitLab** — github.com is blocked; do not reference it in any code or docs
- **Minimal dependencies** — only what is strictly needed

---

## Dependencies (requirements.txt)

```
pyyaml    # config.yaml parsing
click     # CLI argument parsing
```

That is all. No API clients, no graph drivers — the agent owns those concerns.

---

## Trigger conditions (context only — not enforced in v1)

This tool is intended to run after:
- Preflight check has passed (blast radius confirmed, regulatory nodes identified)
- GitLab issue is labelled **AFK** (not HITL)

The orchestrator trusts the developer to run it at the right time. Label enforcement can be added in v2 if needed.

---

## What this is NOT responsible for

- Fetching issue details — the agent does this via GitLab MCP
- Querying the knowledge graph — the agent does this via document/code graph MCP
- Opening the MR — the agent does this via GitLab MCP
- Running the full Cucumber suite — Jenkins does this post-merge
- Managing the remote → integration MR chain — the developer does this manually
