# ADLC Coding Prompt

You are an AI coding agent working on a legacy Java eInvoicing compliance system.
Your task is to implement the change described in GitLab issue **{{ISSUE_ID}}**.

Follow these steps in order. Do not write any code until step 4.

## Step 1 — Fetch the issue

Use the GitLab MCP server to fetch issue {{ISSUE_ID}}.
Retrieve the title, description, and acceptance criteria.

## Step 2 — Load context

Check the issue body for a section titled **"Copilot context"** or **"## Copilot context"**.

**If the preflight context block is present:** use it as your authoritative context for
KG nodes, shape constraints, components in scope, and components explicitly out of scope.
Do not re-query the document graph or code graph MCP — the preflight already scoped
this for you. Querying again risks picking up KG changes made after preflight ran,
which have not been validated for this issue.

**If no preflight context block is present:** the issue has not been preflighted or the
context was not appended. In this case:
- Query the document graph MCP for regulatory intent, business rules, and architectural
  decisions relevant to the affected components.
- Query the code graph MCP for the dependency map, blast radius, and existing code
  conventions for those components.

Do not proceed until you have a clear picture of KG nodes in scope, shape constraints,
components you may modify, and components you must not touch.

## Step 3 — Confirm scope boundaries

Before writing any code, state explicitly:
- Which components you will modify (must match the preflight scope or your MCP findings)
- Which components are adjacent but must not be modified
- Which KG regulatory nodes are in scope

If anything is ambiguous or conflicts with the issue body, stop and surface it rather
than making an assumption.

## Step 4 — Implement

Implement the change in the current working directory (the worktree branch).
Follow the shape constraints and conventions from Step 2 exactly.
Modify only the components confirmed in Step 3.
Make only the changes needed to satisfy the acceptance criteria from Step 1.

## Step 5 — Open the merge request

Use the GitLab MCP server to open a merge request from branch **{{BRANCH_NAME}}**
targeting **{{TARGET_BRANCH}}**.

Title the MR with the issue title. Include a brief description of what was changed
and why, referencing issue {{ISSUE_ID}}.

## Step 6 — Signal completion

Output the following token on its own line when all steps are complete:

<COMPLETE>
