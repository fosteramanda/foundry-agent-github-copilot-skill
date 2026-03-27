# Metrics Agent — Example

A custom engine agent that runs KQL queries against Azure Data Explorer, generates charts, and produces a one-page weekly metrics report. Designed for feature teams who track adoption, retention, and reliability from Kusto telemetry.

## What It Does

- Executes a set of KQL queries against one or more Kusto clusters on a weekly cadence
- Generates sparkline trend charts and funnel visualizations with matplotlib
- Writes a one-page visual report (Markdown + Word) with key signals, trends, and a watchlist
- Tracks week-over-week and 4-week-average changes automatically

## How It Works

Unlike the other example agents (which call a Foundry agent endpoint), this is a **custom engine agent** — a Copilot agent definition (`.md` file) that orchestrates tools directly. It uses the Azure MCP server's Kusto tools to run queries and Python for chart generation. No Foundry agent deployment required.

> **Important: Custom engine agents vs. skills**
>
> This agent is **not** a Copilot skill. Skills live in `.github/skills/` (repo-level) or `~/.copilot/skills/` (user-level) and are invoked via `/skill-name`. Custom engine agents are different — they live in **`~/.copilot/agents/`** and are invoked via `@agent-name` or `/agent agent-name`.
>
> | Concept | Where it lives | How to invoke |
> |---------|---------------|---------------|
> | **Skill** | `~/.copilot/skills/<name>/SKILL.md` | `/skill-name` |
> | **Custom engine agent** | `~/.copilot/agents/<name>.md` | `@name` or `/agent name` |
>
> The `metrics-agent.md` file in this example must be copied to `~/.copilot/agents/`, **not** into the skill directory.

```
┌─────────────────┐     ┌──────────────┐     ┌──────────────┐
│  Copilot CLI     │────▶│  Azure MCP   │────▶│  Kusto/ADX   │
│  (agent runner)  │     │  (KQL tool)  │     │  (your data) │
└────────┬────────┘     └──────────────┘     └──────────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────┐
│  Python          │────▶│  charts/     │
│  (matplotlib)    │     │  report.md   │
└─────────────────┘     │  report.docx │
                        └──────────────┘
```

## Prerequisites

1. **Azure CLI** — Authenticated with access to your Kusto cluster(s)
2. **Python 3.8+** with `matplotlib` and `python-docx`
3. **KQL queries** — `.kql` files in a `metrics/` folder
4. **Kusto cluster access** — Your Azure identity must have reader access to the target databases

## Setup

### 1. Create your agent definition

Copy `metrics-agent.md` to the **agents directory** (not the skills directory):

```
~/.copilot/agents/                      # ← agents go HERE
├── my-team-metrics.md                  # your customized agent definition
├── metrics/                            # KQL query files
│   ├── weekly-usage.kql
│   └── ...
└── weekly-update/                      # report output
    ├── charts/                         # generated charts go here
    ├── weekly-report-template.md
    └── weekly-report-template.docx
```

> ⚠️ **Do not** put the `.md` file in `~/.copilot/skills/`. That directory is for skills (which use `SKILL.md` + tool scripts). Custom engine agents are standalone `.md` files that go in `~/.copilot/agents/`.

### 2. Create your KQL queries

Add `.kql` files to a `metrics/` folder **inside the agents directory** (sibling to your agent `.md` file):

```
~/.copilot/agents/metrics/
├── weekly-usage.kql            # total usage counts, WoW, Wo4W
├── weekly-customers.kql        # unique customers per week
├── top-customers.kql           # top N customers by usage
├── funnel.kql                  # conversion funnel steps
├── reliability.kql             # SLA and latency metrics
└── retention.kql               # churn and retention rates
```

The agent definition references these files by name in its **Cluster Quick-Reference** table.

### 3. Edit the agent definition

Open `metrics-agent.md` and customize these sections:

| Section | What to change |
|---------|----------------|
| **Role** | Your team name, feature name, audience |
| **Glossary** | Your domain terms (e.g., "Workspaces" instead of "Applications") |
| **Queries to Run** | Your `.kql` filenames, cluster URIs, and database names |
| **Report Structure** | Your key signal areas, funnel steps, health thresholds |
| **Chart Generation** | Your sparkline metrics and colors |

### 4. Run it

```
copilot
> /agent my-team-metrics
> analyze my weekly metrics
```

Or without the agent command:
```
> @my-team-metrics generate the weekly report
```

## Customization Guide

### Adding a query

1. Write your KQL query and save it as a `.kql` file in `metrics/`
2. Add a row to the **Cluster Quick-Reference** table in the agent definition
3. Add a description to the **Query Details** section
4. Map it to a report section (Key Signals, Trends, Funnel, or Watchlist)

### Changing the report structure

The template uses 4 sections. You can:

- **Rename sections** — e.g., "Publishing Funnel" → "Onboarding Funnel"
- **Change the funnel steps** — Update step names and event mappings
- **Adjust health thresholds** — Set your own 🟢/🟡/🔴 criteria
- **Add/remove sparklines** — The Trends section supports any number of charts
- **Change the watchlist** — Add OKR tables, remove customer concentration, etc.

### Changing chart colors

Update the hex colors in the Chart Generation section:

| Use case | Suggested palette |
|----------|-------------------|
| Growth metric | Green `#16A34A` |
| Volume metric | Blue `#2563EB` |
| Warning metric | Amber `#D97706` |
| Decline metric | Red `#DC2626` |

## Example Prompts

| What You Say | What the Agent Does |
|---|---|
| "Analyze my weekly metrics" | Runs all queries, generates charts, writes the full report |
| "Show me this week's numbers" | Runs queries and summarizes in chat |
| "Regenerate the charts" | Re-runs chart generation with latest data |
| "What's the trend on customer growth?" | Answers from query results |
| "Document the queries" | Generates a `metrics/README.md` catalog of all `.kql` files |

## Tips

- **Week boundary**: Define yours clearly (e.g., Saturday→Friday, Monday→Sunday). KQL queries should use consistent anchoring.
- **dcount() tolerance**: Kusto's HyperLogLog has ±2% variance. Don't flag small discrepancies between queries.
- **One page rule**: If the report doesn't fit on one page, cut narrative — never cut charts or metric cards.
- **UTF-8 encoding**: On Windows, use `[System.IO.File]::WriteAllText()` or PowerShell's `Set-Content -Encoding utf8` instead of the `create` tool (which writes UTF-16).
- **Template-based docx**: Create a Word template with placeholder tokens and swap values — don't build `.docx` from scratch.
