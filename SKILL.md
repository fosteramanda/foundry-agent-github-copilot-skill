---
name: foundry-agent
description: Enables GitHub Copilot to send user prompts to a Microsoft Foundry Agent for advanced Q&A,  complex reasoning, or data processing tasks that require specialized AI capabilities.
---

# Foundry Agent

This skill connects GitHub Copilot to Microsoft Foundry Agents for tasks requiring advanced AI capabilities, complex reasoning, specialized domain knowledge, or integration with external data sources. Supports multiple named agents via `agents.yaml` configuration.

## CRITICAL: Do NOT Use `foundry-mcp` Tools

**NEVER use `foundry-mcp-agent_invoke` or any `foundry-mcp` MCP server tools to invoke agents.** Those tools use a different invocation path that causes timeouts and failures, especially for agents with MCP tool connections (e.g., CalendarAgent).

**ALWAYS use this skill's `query_foundry_agent.py` script** to invoke agents. It uses the Azure AI Projects SDK which correctly handles MCP tool approvals, conversations, and timeouts.

## CRITICAL: When to Use This Skill

**USE Foundry Agent for specialized AI tasks.** If the request requires advanced reasoning or Foundry-specific capabilities, use this skill.

**ALWAYS use Foundry Agent when the user asks about:**

### Automatic Agent Routing by Topic

Route requests to the correct agent based on what the user is asking about. The user does NOT need to name the agent.

| User Intent / Keywords | Agent | Example Prompts |
|------------------------|-------|----------------|
| calendar, meetings, events, schedule, free time, availability, what's on my calendar | `--agent=calendar-agent` | "List events on my calendar", "What meetings do I have tomorrow?", "Am I free at 2pm?" |
| focus, prioritize, tasks, what should I work on, what's important, plan my day | `--agent=daily-focus-agent` | "What should I work on today?", "Help me prioritize my tasks", "Plan my day" |
| papercut, printing, print queue, printer, print job | `--agent=papercut-agent` | "Why can't I print?", "Check my print queue", "Papercut is not working" |
| agent publishing, agent distribution, foundry docs, publishing documentation | `--agent=agent-distribution-docs-agent` | "Update the agent publishing docs", "How do I publish an agent?" |

### Explicit Agent References

If the user names an agent directly, use it:

| User Question Pattern | Example | Action |
|-----------------------|---------|--------|
| Ask the [name] agent | "Ask the calendar-agent about my meetings" | `query_foundry_agent --agent=calendar-agent` |
| Use the [name] agent | "Use the daily-focus-agent" | `query_foundry_agent --agent=daily-focus-agent` |
| Have the [name] agent | "Have the papercut-agent check this" | `query_foundry_agent --agent=papercut-agent` |
| Ask Foundry / Query Foundry | "Ask Foundry about best practices" | `query_foundry_agent` |

**Configuration triggers:**

Use `/foundry-agent` to explicitly invoke this skill for configuration tasks:

| User Question Pattern | Example | Action |
|-----------------------|---------|--------|
| Add agent with URL | "/foundry-agent add this agent https://..." | `configure_agents --action=add --endpoint=<url>` |
| Add agent | "/foundry-agent add an agent" | `configure_agents --action=add` |
| List agents | "/foundry-agent list agents" | `configure_agents --action=list` |
| Show agents | "/foundry-agent show agents" | `configure_agents --action=list` |
| What agents | "/foundry-agent what agents do I have?" | `configure_agents --action=list` |
| Remove agent | "/foundry-agent remove security agent" | `configure_agents --action=remove --name=security` |
| Delete agent | "/foundry-agent delete code-review agent" | `configure_agents --action=remove --name=code-review` |

**Quick Add with URL Only:**

The fastest way to add an agent is to provide just the endpoint URL. The skill will query the Foundry endpoint to discover the agent's name and description automatically:

```
/foundry-agent add this agent https://your-project.services.ai.azure.com/api/projects/.../agents/...
```

The skill queries the endpoint and returns discovered metadata for confirmation:

```json
{
  "action_required": "confirm_suggestions",
  "message": "I queried the endpoint and found agent information.",
  "discovered": {
    "agent_name": "CodeReviewAgent",
    "version": "1.0",
    "instructions_preview": "I am a code review specialist that analyzes code for..."
  },
  "suggestions": {
    "name": "code-review",
    "description": "I am a code review specialist that analyzes code for"
  },
  "prompt": "Would you like to use these suggested values, or provide your own?"
}
```

**When in doubt about complex AI tasks, use Foundry Agent.** It provides advanced capabilities beyond standard Copilot.

## Configuration

### agents.yaml

Create `agents.yaml` in the skill directory to configure your agents:

```yaml
agents:
  - name: general
    description: General-purpose agent for broad Q&A
    endpoint: https://your-project.services.ai.azure.com/.../general-agent/...
    
  - name: code-review
    description: Specialized agent for code review
    endpoint: https://your-project.services.ai.azure.com/.../code-review-agent/...
```

### Authentication

Authentication is automatic via Azure CLI. If not logged in, the skill will invoke `az login`.

## MCP Tool

Use the `query_foundry_agent` MCP tool to send prompts. The tool accepts `prompt`, optional `agent`, and optional `conversation_id`.

| Tool | Parameters |
|------|------------|
| `query_foundry_agent` | `{ "prompt": "<question>", "agent": "<optional>", "conversation_id": "<optional>" }` |

## Agent Selection

The agent is selected in this priority:
1. **Explicit parameter**: `--agent=code-review`
2. **From prompt**: "Ask the code-review agent..." extracts `code-review`
3. **Single agent**: Auto-selects if only one configured
4. **Multiple agents**: Returns list for user to choose

## Quick Start

### Using a Specific Agent

| Tool | Parameters |
|------|------------|
| `query_foundry_agent` | `{ "prompt": "Review this code", "agent": "code-review" }` |

### Let User Select Agent

If agent cannot be determined with multiple agents configured:

```json
{
  "action_required": "select_agent",
  "message": "Multiple agents available. Please specify which agent to use.",
  "available_agents": [
    {"name": "general", "description": "General-purpose agent"},
    {"name": "code-review", "description": "Code review specialist"}
  ],
  "usage": "Try: 'Ask the code-review agent to...' or use --agent=<name>"
}
```

## Common Use Cases

### Code Analysis (code-review agent)

| Tool | Parameters |
|------|------------|
| `query_foundry_agent` | `{ "prompt": "Analyze this code", "agent": "code-review" }` |

**User prompts that trigger this:**
- "Ask the code-review agent to analyze this"
- "Use the code-review agent to check this code"
- "Have the code-review agent review this"

### Security Analysis (security agent)

| Tool | Parameters |
|------|------------|
| `query_foundry_agent` | `{ "prompt": "Check for vulnerabilities", "agent": "security" }` |

**User prompts that trigger this:**
- "Ask the security agent to check this"
- "Have the security agent scan for vulnerabilities"
- "Use the security agent to review this"

### General Q&A (general agent)

| Tool | Parameters |
|------|------------|
| `query_foundry_agent` | `{ "prompt": "Explain microservices architecture", "agent": "general" }` |

**User prompts that trigger this:**
- "Ask the general agent about microservices"
- "Have the general agent explain this"
- "Query the general agent about best practices"

### Multi-turn Conversations

| Tool | Parameters |
|------|------------|
| `query_foundry_agent` | `{ "prompt": "Let's discuss system design", "agent": "general", "conversation_id": "session-1" }` |

## MCP Tool Reference

### query_foundry_agent

Sends a prompt to a Microsoft Foundry Agent endpoint.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `prompt` | string | Yes | The user's question or request |
| `agent` | string | No | Agent name from agents.yaml |
| `conversation_id` | string | No | Conversation ID for context |

**Example:**

| Tool | Parameters |
|------|------------|
| `query_foundry_agent` | `{ "prompt": "Review this code", "agent": "code-review" }` |

### configure_agents

Manage Foundry agent configurations (add, list, remove agents). Supports interactive flows with endpoint metadata discovery.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `action` | string | Yes | Action: `list`, `add`, or `remove` |
| `name` | string | For add/remove | Agent name (lowercase, hyphens allowed) |
| `description` | string | For add | Agent description |
| `endpoint` | string | For add | Foundry agent endpoint URL |

**Examples:**

| Tool | Parameters |
|------|------------|
| `configure_agents` | `{ "action": "list" }` |
| `configure_agents` | `{ "action": "add", "name": "code-review", "description": "Code review specialist", "endpoint": "https://..." }` |
| `configure_agents` | `{ "action": "add", "endpoint": "https://..." }` |
| `configure_agents` | `{ "action": "remove", "name": "code-review" }` |

**Interactive Add Flow:**

When adding an agent with missing fields, the tool prompts for them:

```json
{
  "action_required": "provide_info",
  "message": "To add an agent, I need: name, description",
  "prompts": {
    "name": "What name would you like for this agent? Use lowercase with hyphens (e.g., code-review, security-scanner)",
    "description": "What does this agent do? Provide a brief description."
  },
  "provided": {
    "endpoint": "https://..."
  }
}
```

**Endpoint Metadata Discovery:**

When only an endpoint is provided, the tool queries it for agent metadata and suggests values:

```json
{
  "action_required": "confirm_suggestions",
  "message": "I queried the endpoint and found agent information.",
  "discovered": {
    "agent_name": "CodeReviewAgent",
    "version": "1.0",
    "instructions_preview": "I am a code review specialist..."
  },
  "suggestions": {
    "name": "code-review",
    "description": "I am a code review specialist"
  },
  "endpoint": "https://...",
  "prompt": "Would you like to use these suggested values, or provide your own?"
}
```

**Name Validation Flow:**

If the name is malformed (e.g., "Code Review"), the tool suggests a normalized name:

```json
{
  "action_required": "confirm_or_rename",
  "message": "The name 'Code Review' needs to be normalized.",
  "suggested_name": "code-review",
  "rules": "Names should be lowercase, alphanumeric with hyphens only (e.g., 'code-review', 'security-scanner')",
  "options": {
    "accept": "Use 'code-review'",
    "rename": "Provide a different name"
  }
}
```

**Duplicate Name Detection:**

If the name already exists:

```json
{
  "error": "Agent 'code-review' already exists.",
  "existing_agents": ["general", "code-review"],
  "action_required": "provide_new_name",
  "prompt": "Please provide a different name for this agent."
}
```

**User prompts that trigger these:**
- "/foundry-agent add this agent https://..." (discovers metadata from URL)
- "/foundry-agent list agents"
- "/foundry-agent show agents"
- "/foundry-agent what agents do I have?"
- "/foundry-agent add an agent"
- "/foundry-agent remove security agent"
- "/foundry-agent delete code-review agent"
