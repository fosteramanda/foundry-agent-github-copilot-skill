# Documentation Agent — Example

A documentation management agent that reads, edits, and commits changes to a set of Markdown files in a GitHub repository using the GitHub MCP tool.

## What It Does

- Manages a defined set of documentation files in a GitHub repo
- Always reads current file contents before making edits (never assumes)
- Commits changes with descriptive messages directly to the target branch
- Preserves existing document structure and formatting

## Prerequisites

1. **A GitHub repository** with the documentation files you want the agent to manage
2. **A Foundry agent** created in [Azure AI Foundry](https://ai.azure.com) with:
   - The [documentation-agent.md](documentation-agent.md) as the agent's instructions
   - A GitHub MCP tool connection (for reading/writing files and committing)

## Setup

1. **Edit `documentation-agent.md`** — Replace the placeholders:
   - `<owner>/<repo>` → your GitHub repo (e.g., `myorg/my-docs`)
   - `<branch>` → target branch (e.g., `main`)
   - `<file-N>.md` and `<path/to/file-N>.md` → the files the agent should manage

2. **Create the agent in Foundry** — Paste the edited prompt as the agent's instructions and connect the GitHub MCP tool

3. **Add to agents.yaml** in your skill:
   ```yaml
   - name: docs-agent
     description: Manages and updates documentation files in GitHub
     agent_name: DocsAgent
   ```

## Example Prompts

| What You Say | What the Agent Does |
|---|---|
| "Update the getting-started guide with the new API endpoint" | Reads the file, applies the change, commits |
| "Add a troubleshooting section to file-1.md" | Reads current content, appends section, commits |
| "Fix the typo in the setup instructions" | Reads file, corrects it, commits with descriptive message |
| "What's currently in the deployment guide?" | Fetches and displays the file contents |
