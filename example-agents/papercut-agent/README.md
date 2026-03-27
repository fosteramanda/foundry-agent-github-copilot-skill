# Papercut Agent — Example

A bug-tracking agent that retrieves, displays, and analyzes "papercut" (small customer-facing issues) work items from Azure DevOps.

## What It Does

- Fetches active and closed papercut work items from ADO saved queries
- Displays results in clean tables with links to work items
- Analyzes owner workload, aging, velocity, and risks
- Answers natural language questions like "what was fixed this week?" or "who has the most papercuts?"

## Prerequisites

1. **Azure DevOps saved queries** — Create two shared queries in your ADO project:
   - **Active papercuts**: Filters work items tagged with your team tag + `papercut` in active states (New, Active, In Progress, etc.)
   - **Closed papercuts**: Same tags but in terminal states (Done, Resolved, Removed)

2. **A Foundry agent** — Create an agent in [Azure AI Foundry](https://ai.azure.com) with:
   - The [papercut-agent-prompt.md](papercut-agent-prompt.md) as the agent's instructions
   - An Azure DevOps MCP tool connection (for `wit_get_query_results_by_id`)

## Setup

1. **Create your ADO saved queries** and note their query GUIDs

2. **Edit `papercut-agent-prompt.md`** — Replace the placeholders:
   - `<your-ado-org>` → your ADO organization name
   - `<your-ado-project>` → your ADO project name
   - `<your-team-tag>` → your team's tag (e.g., `MyTeam`)
   - `<query-guid>` → the GUIDs of your saved queries

3. **Create the agent in Foundry** — Paste the edited prompt as the agent's instructions

4. **Add to agents.yaml** in your skill:
   ```yaml
   - name: papercut-agent
     description: Retrieves and analyzes papercut work items from Azure DevOps
     agent_name: PapercutAgent
   ```

## Example Prompts

| What You Say | What the Agent Does |
|---|---|
| "Show me the papercuts" | Fetches and displays active + recently closed tables |
| "What was fixed this week?" | Filters closed items by date, shows all results |
| "Who has the most papercuts?" | Groups active items by owner, ranks them |
| "Any past-due items?" | Filters active items where ETA < today |
| "Analyze the papercuts" | Full analysis: summary, workload, aging, velocity, risks |
