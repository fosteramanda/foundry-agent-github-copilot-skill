#!/usr/bin/env python3
"""
GitHub Copilot Agent Skill tool: query_foundry_agent
Sends a prompt to Microsoft Foundry Agent for advanced AI processing.
Supports multiple agents via agents.yaml configuration.
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
        return True
    except ImportError:
        print(json.dumps({
            "error": "Missing dependencies. Run: cd ~/.copilot/skills/foundry-agent && source .venv/bin/activate && uv pip install pyyaml requests azure-identity azure-ai-projects python-dotenv"
        }))
        sys.exit(1)


ensure_dependencies()

import yaml

# Path to agents config relative to this script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AGENTS_CONFIG_PATH = os.path.join(SCRIPT_DIR, "agents.yaml")


def get_azure_credential():
    """Lazy-load Azure credentials (azure-identity is slow to import)."""
    from azure.identity import DefaultAzureCredential, AzureCliCredential
    from azure.core.exceptions import ClientAuthenticationError
    return DefaultAzureCredential, AzureCliCredential, ClientAuthenticationError


def load_agents_config():
    """Load agents configuration from agents.yaml if it exists."""
    if os.path.exists(AGENTS_CONFIG_PATH):
        with open(AGENTS_CONFIG_PATH, 'r') as f:
            config = yaml.safe_load(f)
            return config.get('agents', [])
    return []


def extract_agent_from_prompt(prompt: str, agents: list) -> str | None:
    """Extract agent name from prompt using pattern matching."""
    agent_names = [a['name'] for a in agents]
    patterns = [
        r"ask (?:the )?(\w+[\w-]*) agent",
        r"use (?:the )?(\w+[\w-]*) agent", 
        r"query (?:the )?(\w+[\w-]*) agent",
        r"(?:the )?(\w+[\w-]*) agent to",
        r"have (?:the )?(\w+[\w-]*) (?:agent )?(?:analyze|review|check|scan|calculate|compute|rate|prioritize)",
        r"send (?:this )?to (?:the )?(\w+[\w-]*) agent",
        r"let (?:the )?(\w+[\w-]*) agent",
    ]
    
    prompt_lower = prompt.lower()
    for pattern in patterns:
        match = re.search(pattern, prompt_lower)
        if match:
            extracted = match.group(1)
            for name in agent_names:
                if name.lower() == extracted or name.lower().replace('-', '') == extracted:
                    return name
    return None


def get_agent_endpoint(agent_name: str | None, prompt: str) -> dict:
    """
    Get the endpoint for the specified agent.
    Returns dict with agent configuration on success, or 'select_agent' response if ambiguous.
    Supports both project endpoint (agent_name) and application endpoint (endpoint) styles.
    """
    agents = load_agents_config()
    
    if not agents:
        return {
            "error": "No agents configured. Create agents.yaml with your agent endpoints.",
            "help": "Copy agents.yaml.example to agents.yaml and configure your agents."
        }
    
    # If agent specified via parameter, use it
    if agent_name:
        for agent in agents:
            if agent['name'].lower() == agent_name.lower():
                # Check if using project endpoint style (agent_name) or application endpoint style (endpoint)
                if 'agent_name' in agent:
                    # Load project endpoint from config
                    with open(AGENTS_CONFIG_PATH, 'r') as f:
                        config = yaml.safe_load(f)
                        project_endpoint = config.get('project_endpoint')
                    result = {
                        "style": "project",
                        "project_endpoint": project_endpoint,
                        "agent_name": agent['agent_name'],
                        "display_name": agent['name']
                    }
                    if 'agent_version' in agent:
                        result['agent_version'] = agent['agent_version']
                    return result
                elif 'endpoint' in agent:
                    return {
                        "style": "application",
                        "endpoint": agent['endpoint'],
                        "display_name": agent['name']
                    }
                else:
                    return {
                        "error": f"Agent '{agent_name}' missing both 'agent_name' and 'endpoint' configuration"
                    }
        return {
            "error": f"Agent '{agent_name}' not found",
            "available_agents": [{"name": a['name'], "description": a['description']} for a in agents]
        }
    
    # Try to extract agent from prompt
    extracted = extract_agent_from_prompt(prompt, agents)
    if extracted:
        for agent in agents:
            if agent['name'] == extracted:
                # Check if using project endpoint style or application endpoint style
                if 'agent_name' in agent:
                    with open(AGENTS_CONFIG_PATH, 'r') as f:
                        config = yaml.safe_load(f)
                        project_endpoint = config.get('project_endpoint')
                    result = {
                        "style": "project",
                        "project_endpoint": project_endpoint,
                        "agent_name": agent['agent_name'],
                        "display_name": agent['name']
                    }
                    if 'agent_version' in agent:
                        result['agent_version'] = agent['agent_version']
                    return result
                elif 'endpoint' in agent:
                    return {
                        "style": "application",
                        "endpoint": agent['endpoint'],
                        "display_name": agent['name']
                    }
    
    # Single agent configured - use it automatically
    if len(agents) == 1:
        agent = agents[0]
        if 'agent_name' in agent:
            with open(AGENTS_CONFIG_PATH, 'r') as f:
                config = yaml.safe_load(f)
                project_endpoint = config.get('project_endpoint')
            result = {
                "style": "project",
                "project_endpoint": project_endpoint,
                "agent_name": agent['agent_name'],
                "display_name": agent['name']
            }
            if 'agent_version' in agent:
                result['agent_version'] = agent['agent_version']
            return result
        elif 'endpoint' in agent:
            return {
                "style": "application",
                "endpoint": agent['endpoint'],
                "display_name": agent['name']
            }
    
    # Multiple agents, can't determine - ask user to select
    return {
        "action_required": "select_agent",
        "message": "Multiple agents available. Please specify which agent to use.",
        "available_agents": [{"name": a['name'], "description": a['description']} for a in agents],
        "usage": "Try: 'Ask the code-review agent to...' or use --agent=<name>"
    }


def query_foundry_agent(prompt: str, conversation_id: str = None, agent_name: str = None):
    """
    Query the Microsoft Foundry Agent with a user prompt.
    Supports both project endpoint and application endpoint styles.
    
    Args:
        prompt: The user's question or request to send to the Foundry Agent
        conversation_id: Optional conversation ID for maintaining context
        agent_name: Optional agent name to use (from agents.yaml)
        
    Returns:
        dict: The Foundry Agent response or error information
    """
    # Resolve agent configuration
    agent_config = get_agent_endpoint(agent_name, prompt)
    
    if "error" in agent_config or "action_required" in agent_config:
        return agent_config
    
    style = agent_config.get("style")
    display_name = agent_config.get("display_name", "default")
    
    try:
        if style == "project":
            # Use Azure AI Projects SDK (project endpoint style)
            return _query_via_project_endpoint(
                prompt=prompt,
                conversation_id=conversation_id,
                project_endpoint=agent_config["project_endpoint"],
                agent_name=agent_config["agent_name"],
                agent_version=agent_config.get("agent_version"),
                display_name=display_name
            )
        elif style == "application":
            # Use direct HTTP requests (application endpoint style)
            return _query_via_application_endpoint(
                prompt=prompt,
                conversation_id=conversation_id,
                endpoint=agent_config["endpoint"],
                display_name=display_name
            )
        else:
            return {"error": f"Unknown agent style: {style}"}
            
    except Exception as e:
        return {
            "error": f"Unexpected error: {str(e)}",
            "type": type(e).__name__,
            "agent": display_name
        }


def _query_via_project_endpoint(prompt: str, conversation_id: str, project_endpoint: str, 
                                  agent_name: str, display_name: str, agent_version: str = None) -> dict:
    """Query agent using Azure AI Projects SDK (project endpoint)."""
    try:
        from azure.identity import DefaultAzureCredential
        from azure.ai.projects import AIProjectClient
        from openai.types.responses.response_input_param import McpApprovalResponse, ResponseInputParam
        
        with (
            DefaultAzureCredential() as credential,
            AIProjectClient(endpoint=project_endpoint, credential=credential) as project_client,
            project_client.get_openai_client() as openai_client,
        ):
            # Optionally get specific agent version (useful for email agent, etc.)
            if agent_version:
                agent = project_client.agents.get_version(
                    agent_name=agent_name,
                    agent_version=agent_version,
                )
                agent_ref_name = agent.name  # Use the actual agent name from the version
            else:
                agent_ref_name = agent_name
            
            # Create or use existing conversation
            if conversation_id:
                # Use existing conversation
                conv_id = conversation_id
            else:
                # Create new conversation
                conversation = openai_client.conversations.create()
                conv_id = conversation.id
            
            # Send the question
            response = openai_client.responses.create(
                conversation=conv_id,
                input=prompt,
                extra_body={"agent_reference": {"name": agent_ref_name, "type": "agent_reference"}},
            )
            
            # Process any MCP approval requests that were generated
            input_list: ResponseInputParam = []
            for item in response.output:
                if item.type == "mcp_approval_request":
                    if item.id:
                        # Automatically approve the MCP request
                        input_list.append(
                            McpApprovalResponse(
                                type="mcp_approval_response",
                                approve=True,
                                approval_request_id=item.id,
                            )
                        )
            
            # Send the approval response back if there were any approval requests
            if input_list:
                response = openai_client.responses.create(
                    input=input_list,
                    previous_response_id=response.id,
                    extra_body={"agent_reference": {"name": agent_ref_name, "type": "agent_reference"}},
                )
            
            return {
                "output_text": response.output_text,
                "conversation_id": conv_id,
                "response_id": response.id,
                "_agent_used": display_name,
                "_style": "project"
            }
            
    except Exception as e:
        error_message = str(e)
        error_dict = {
            "error": f"Failed to call Foundry Agent via project endpoint: {error_message}",
            "agent": display_name,
            "endpoint": project_endpoint
        }
        
        # Detect specific error types for better handling
        if "TimeoutPolicy" in error_message or "did not complete within the timeout" in error_message:
            error_dict["error_type"] = "timeout"
            error_dict["retry_hint"] = "The remote MCP tool timed out. You can retry the same question."
        elif "Failed to fetch access token" in error_message or "getuseraccesstoken" in error_message:
            error_dict["error_type"] = "auth_token"
            error_dict["retry_hint"] = "Could not get a delegated user token. Re-authenticate: az logout && az login --tenant '72f988bf-86f1-41af-91ab-2d7cd011db47' --scope 'https://ai.azure.com/.default'"
        
        return error_dict


def _query_via_application_endpoint(prompt: str, conversation_id: str, endpoint: str, 
                                      display_name: str) -> dict:
    """Query agent using direct HTTP requests (application endpoint)."""
    try:
        import requests
        from azure.identity import DefaultAzureCredential, AzureCliCredential
        
        credential = DefaultAzureCredential()
        token = credential.get_token("https://ai.azure.com/.default")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token.token}"
        }
        
        payload = {"input": prompt}
        if conversation_id:
            payload["previous_response_id"] = conversation_id
        
        response = requests.post(endpoint, json=payload, headers=headers, timeout=120)
        response.raise_for_status()
        result = response.json()
        result["_agent_used"] = display_name
        result["_style"] = "application"
        return result
        
    except requests.exceptions.RequestException as e:
        error_message = str(e)
        error_dict = {
            "error": f"Failed to call Foundry Agent: {error_message}",
            "endpoint": endpoint,
            "agent": display_name
        }
        
        # Detect specific error types
        if "TimeoutPolicy" in error_message or "did not complete within the timeout" in error_message or "timeout" in error_message.lower():
            error_dict["error_type"] = "timeout"
            error_dict["retry_hint"] = "The remote MCP tool timed out. You can retry the same question."
        
        return error_dict
    except Exception as e:
        # Check if it's an auth error
        error_message = str(e)
        if "ClientAuthenticationError" in type(e).__name__ or "authentication" in error_message.lower():
            try:
                subprocess.run(["az", "login"], check=True)
                credential = AzureCliCredential()
                token = credential.get_token("https://ai.azure.com/.default")
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {token.token}"
                }
                payload = {"input": prompt}
                if conversation_id:
                    payload["previous_response_id"] = conversation_id
                response = requests.post(endpoint, json=payload, headers=headers, timeout=120)
                response.raise_for_status()
                result = response.json()
                result["_agent_used"] = display_name
                result["_style"] = "application"
                return result
            except subprocess.CalledProcessError:
                return {
                    "error": "Azure login failed. Please run 'az login' manually.",
                    "error_type": "auth_login"
                }
            except Exception as e2:
                error_message2 = str(e2)
                error_dict = {"error": f"Authentication retry failed: {error_message2}"}
                
                # Check for token errors in retry
                if "Failed to fetch access token" in error_message2 or "getuseraccesstoken" in error_message2:
                    error_dict["error_type"] = "auth_token"
                    error_dict["retry_hint"] = "Could not get a delegated user token. Re-authenticate: az logout && az login --tenant '72f988bf-86f1-41af-91ab-2d7cd011db47' --scope 'https://ai.azure.com/.default'"
                
                return error_dict
        
        return {"error": f"Unexpected error: {error_message}", "type": type(e).__name__}


def main():
    """Main entry point for the tool when called by GitHub Copilot."""
    try:
        parser = argparse.ArgumentParser(description="Query Microsoft Foundry Agent")
        parser.add_argument("prompt", help="The user's question or request")
        parser.add_argument("--conversation_id", "-c", help="Conversation ID for context", default=None)
        parser.add_argument("--agent", "-a", help="Agent name to use (from agents.yaml)", default=None)
        
        args = parser.parse_args()
        result = query_foundry_agent(args.prompt, args.conversation_id, args.agent)
        print(json.dumps(result))
        
    except Exception as e:
        print(json.dumps({"error": f"Tool execution failed: {str(e)}"}))
        sys.exit(1)


if __name__ == "__main__":
    main()
