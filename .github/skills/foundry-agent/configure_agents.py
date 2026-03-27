#!/usr/bin/env python3
"""
GitHub Copilot Agent Skill tool: configure_agents
Manage Foundry agent configurations in agents.yaml.
"""

import os
import sys
import json
import argparse
import subprocess
import re


def ensure_dependencies():
    """Check if dependencies are available."""
    try:
        import yaml
        import requests
        return True
    except ImportError:
        print(json.dumps({
            "error": "Missing dependencies. Run: cd ~/.copilot/skills/foundry-agent && source .venv/bin/activate && uv pip install pyyaml requests azure-identity"
        }))
        sys.exit(1)


ensure_dependencies()

import yaml

# Path to agents config relative to this script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AGENTS_CONFIG_PATH = os.path.join(SCRIPT_DIR, "agents.yaml")


def load_config():
    """Load agents configuration from agents.yaml."""
    if os.path.exists(AGENTS_CONFIG_PATH):
        with open(AGENTS_CONFIG_PATH, 'r') as f:
            config = yaml.safe_load(f)
            return config if config else {"agents": []}
    return {"agents": []}


def save_config(config):
    """Save agents configuration to agents.yaml."""
    with open(AGENTS_CONFIG_PATH, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)


def validate_endpoint(endpoint: str) -> bool:
    """Validate endpoint URL format."""
    pattern = r'^https://[\w\-\.]+\.services\.ai\.azure\.com/.*'
    return bool(re.match(pattern, endpoint))


def query_agent_metadata(endpoint: str) -> dict:
    """Query the Foundry endpoint to get agent metadata (name, instructions)."""
    try:
        # Lazy import - azure-identity is slow to load
        import requests
        from azure.identity import DefaultAzureCredential
        
        credential = DefaultAzureCredential()
        token = credential.get_token("https://ai.azure.com/.default")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token.token}"
        }
        
        # Send minimal request to get agent info
        response = requests.post(endpoint, json={"input": "describe yourself"}, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            agent_info = data.get("agent", {})
            instructions = data.get("instructions", "")
            
            # Extract first sentence of instructions for description
            description = ""
            if instructions:
                # Get first sentence or first 150 chars
                first_sentence = instructions.split('.')[0].strip()
                description = first_sentence[:150] if len(first_sentence) > 150 else first_sentence
            
            return {
                "success": True,
                "name": agent_info.get("name", ""),
                "version": agent_info.get("version", ""),
                "description": description,
                "full_instructions": instructions[:500] if instructions else ""
            }
        else:
            return {"success": False, "error": f"API returned {response.status_code}"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}


def normalize_name(name: str) -> str:
    """Convert name to valid format: lowercase, alphanumeric with hyphens."""
    # Convert to lowercase
    normalized = name.lower().strip()
    # Replace spaces and underscores with hyphens
    normalized = re.sub(r'[\s_]+', '-', normalized)
    # Remove invalid characters (keep only alphanumeric and hyphens)
    normalized = re.sub(r'[^a-z0-9\-]', '', normalized)
    # Remove multiple consecutive hyphens
    normalized = re.sub(r'-+', '-', normalized)
    # Remove leading/trailing hyphens
    normalized = normalized.strip('-')
    return normalized


def normalize_agent_name(name: str) -> str:
    """Convert CamelCase or PascalCase agent name to kebab-case."""
    # Insert hyphens before uppercase letters (for CamelCase)
    name = re.sub(r'([a-z])([A-Z])', r'\1-\2', name)
    # Insert hyphens before sequences of uppercase followed by lowercase
    name = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1-\2', name)
    # Convert to lowercase
    name = name.lower()
    # Remove common suffixes (agent, af, app, etc.)
    name = re.sub(r'[-]?(agent|af|app|-af|-agent)+$', '', name)
    # Apply standard normalization
    return normalize_name(name)


def validate_name(name: str, existing_agents: list) -> dict:
    """Validate agent name and return suggestions if invalid."""
    if not name:
        return {"valid": False, "error": "Name is required"}
    
    normalized = normalize_name(name)
    
    # Check for duplicates
    existing_names = [a['name'].lower() for a in existing_agents]
    if normalized in existing_names:
        return {
            "valid": False,
            "error": f"Agent '{normalized}' already exists.",
            "existing_agents": existing_names,
            "action_required": "provide_new_name",
            "prompt": "Please provide a different name for this agent."
        }
    
    # Check if name needed normalization
    if name != normalized:
        return {
            "valid": False,
            "action_required": "confirm_or_rename",
            "message": f"The name '{name}' needs to be normalized.",
            "suggested_name": normalized,
            "rules": "Names should be lowercase, alphanumeric with hyphens only (e.g., 'code-review', 'security-scanner')",
            "options": {
                "accept": f"Use '{normalized}'",
                "rename": "Provide a different name"
            }
        }
    
    # Validate format
    if not re.match(r'^[a-z][a-z0-9\-]*[a-z0-9]$|^[a-z]$', name):
        suggested = normalized if normalized else "general"
        return {
            "valid": False,
            "action_required": "confirm_or_rename",
            "message": f"The name '{name}' is invalid.",
            "suggested_name": suggested,
            "rules": "Names must start with a letter, contain only lowercase letters, numbers, and hyphens",
            "options": {
                "accept": f"Use '{suggested}'",
                "rename": "Provide a different name"
            }
        }
    
    return {"valid": True, "name": name}


def list_agents():
    """List all configured agents."""
    config = load_config()
    agents = config.get('agents', [])
    
    if not agents:
        return {
            "message": "No agents configured.",
            "help": "Use --action=add to add an agent."
        }
    
    agent_list = []
    for a in agents:
        info = {"name": a['name'], "description": a.get('description', '')}
        if 'endpoint' in a:
            info["endpoint"] = a['endpoint'][:50] + "..."
        if 'agent_name' in a:
            info["agent_name"] = a['agent_name']
        if 'version' in a:
            info["version"] = a['version']
        agent_list.append(info)
    
    return {
        "agents": agent_list,
        "project_endpoint": config.get('project_endpoint', ''),
        "count": len(agents)
    }


def add_agent(name: str, description: str, endpoint: str):
    """Add a new agent to the configuration."""
    config = load_config()
    agents = config.get('agents', [])
    
    # If endpoint is provided but name/description are missing, query the endpoint for metadata
    if endpoint and (not name or not description):
        if validate_endpoint(endpoint):
            metadata = query_agent_metadata(endpoint)
            if metadata.get("success"):
                suggested_name = normalize_agent_name(metadata.get("name", ""))
                suggested_desc = metadata.get("description", "")
                
                return {
                    "action_required": "confirm_suggestions",
                    "message": "I queried the endpoint and found agent information.",
                    "discovered": {
                        "agent_name": metadata.get("name"),
                        "version": metadata.get("version"),
                        "instructions_preview": metadata.get("full_instructions", "")[:200] + "..." if metadata.get("full_instructions") else "None"
                    },
                    "suggestions": {
                        "name": name if name else suggested_name,
                        "description": description if description else suggested_desc
                    },
                    "endpoint": endpoint,
                    "prompt": "Would you like to use these suggested values, or provide your own?"
                }
    
    # Interactive mode - prompt for missing fields
    missing = []
    if not name:
        missing.append("name")
    if not description:
        missing.append("description")
    if not endpoint:
        missing.append("endpoint")
    
    if missing:
        prompts = {
            "name": "What name would you like for this agent? Use lowercase with hyphens (e.g., code-review, security-scanner)",
            "description": "What does this agent do? Provide a brief description.",
            "endpoint": "What is the Foundry agent endpoint URL? (e.g., https://your-project.services.ai.azure.com/api/projects/...)"
        }
        return {
            "action_required": "provide_info",
            "message": f"To add an agent, I need: {', '.join(missing)}",
            "prompts": {field: prompts[field] for field in missing},
            "provided": {
                "name": name,
                "description": description,
                "endpoint": endpoint
            }
        }
    
    # Validate name format and check for duplicates
    name_validation = validate_name(name, agents)
    if not name_validation.get("valid"):
        return name_validation
    
    if not validate_endpoint(endpoint):
        return {
            "error": "Invalid endpoint URL format.",
            "expected": "https://<project>.services.ai.azure.com/api/projects/...",
            "provided": endpoint
        }
    
    # Add new agent
    agents.append({
        "name": name,
        "description": description,
        "endpoint": endpoint
    })
    config['agents'] = agents
    save_config(config)
    
    return {
        "success": True,
        "message": f"Agent '{name}' added successfully.",
        "agent": {"name": name, "description": description}
    }


def remove_agent(name: str):
    """Remove an agent from the configuration."""
    if not name:
        return {"error": "Missing required parameter: --name"}
    
    config = load_config()
    agents = config.get('agents', [])
    
    # Find and remove agent
    original_count = len(agents)
    agents = [a for a in agents if a['name'].lower() != name.lower()]
    
    if len(agents) == original_count:
        return {
            "error": f"Agent '{name}' not found.",
            "available_agents": [a['name'] for a in agents]
        }
    
    config['agents'] = agents
    save_config(config)
    
    return {
        "success": True,
        "message": f"Agent '{name}' removed successfully.",
        "remaining_agents": len(agents)
    }


def main():
    """Main entry point for the tool."""
    try:
        parser = argparse.ArgumentParser(description="Configure Foundry agents")
        parser.add_argument("--action", "-a", required=True, 
                          choices=["list", "add", "remove"],
                          help="Action to perform")
        parser.add_argument("--name", "-n", help="Agent name")
        parser.add_argument("--description", "-d", help="Agent description")
        parser.add_argument("--endpoint", "-e", help="Agent endpoint URL")
        
        args = parser.parse_args()
        
        if args.action == "list":
            result = list_agents()
        elif args.action == "add":
            result = add_agent(args.name, args.description, args.endpoint)
        elif args.action == "remove":
            result = remove_agent(args.name)
        else:
            result = {"error": f"Unknown action: {args.action}"}
        
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(json.dumps({"error": f"Tool execution failed: {str(e)}"}))
        sys.exit(1)


if __name__ == "__main__":
    main()
