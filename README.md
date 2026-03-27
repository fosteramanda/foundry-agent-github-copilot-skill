# Foundry GitHub Copilot Skill

A GitHub Copilot skill that connects to Microsoft Foundry Agent applications. Supports multiple named agents.

## Requirements

- Python 3.8+
- Azure CLI installed

## Setup

Choose **one** of the two options below depending on how you want to use the skill.

### Option A: Add to a GitHub repository

Use this when you want the skill available in a specific project repo (shared with your team via source control).

Copy the skill files into your repo:

```
your-repo/.github/skills/foundry-agent/
├── SKILL.md
├── query_foundry_agent.py
├── configure_agents.py
├── agents.yaml.example
└── agents.yaml          # your config (gitignored)
```

### Option B: Use locally with Copilot CLI

Use this when you want the skill available across all your projects without a GitHub repo. Copy the skill files to your local Copilot skills directory:

```
~/.copilot/skills/foundry-agent/
├── SKILL.md
├── query_foundry_agent.py
├── configure_agents.py
├── agents.yaml.example
└── agents.yaml          # your config
```

No GitHub repo needed — Copilot picks up skills from this directory automatically.

### Configure agents

**Option A: Interactive setup via Copilot (recommended)**

Just ask Copilot to add an agent - it will guide you through:

```
You: "Add a Foundry agent"
Copilot: "What name would you like for this agent?"
You: "code-review"
Copilot: "What does this agent do?"
You: "Code review and best practices"
Copilot: "What is the endpoint URL?"
You: <paste URL>
Copilot: "✓ Agent 'code-review' added!"
```

Names are validated automatically - if you enter "Code Review", it will suggest "code-review".

**Option B: Manual configuration**

Copy `agents.yaml.example` to `agents.yaml` and configure your agents:

```yaml
agents:
  - name: general
    description: General-purpose agent for broad Q&A
    endpoint: https://your-project.services.ai.azure.com/.../general-agent/...

  - name: code-review
    description: Specialized agent for code review
    endpoint: https://your-project.services.ai.azure.com/.../code-review-agent/...
```

> **Note:** Python dependencies and Azure authentication are handled automatically.

## Usage

### Query Agents

- "Ask Foundry about this code"
- "Ask the code-review agent to check this"
- "Have the security agent scan for vulnerabilities"
- "Talk to Foundry about best practices"
- "Query Foundry about architecture patterns"
- "Send this to the general agent"

### Configure Agents

Use `/foundry-agent` to explicitly invoke this skill:

- "/foundry-agent add this agent https://..." - **easiest way** - discovers name/description from the endpoint
- "/foundry-agent add an agent" - interactive guided setup
- "/foundry-agent list agents" - show configured agents
- "/foundry-agent show agents" - show configured agents
- "/foundry-agent remove security agent" - delete an agent

If multiple agents exist and none specified, you'll be prompted to choose.

## Example Agents

The `example-agents/` folder contains ready-to-customize agent templates:

| Agent | Type | Description |
|-------|------|-------------|
| [papercut-agent](example-agents/papercut-agent/) | Foundry Agent | Print queue troubleshooting via a Foundry endpoint |
| [metrics-agent](example-agents/metrics-agent/) | Custom Engine Agent | Weekly KQL metrics → charts → one-page report |

## Resources

- [Microsoft Foundry Docs](https://learn.microsoft.com/azure/ai-foundry/)
- [Copilot Agent Skills](https://code.visualstudio.com/docs/copilot/customization/agent-skills)
