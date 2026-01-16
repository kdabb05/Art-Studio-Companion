"""Letta Agent Configuration for Art Studio Companion."""

import os
from typing import Optional
from letta import create_client, LLMConfig, EmbeddingConfig
from letta.schemas.memory import ChatMemory
from letta.schemas.tool import Tool


# Agent system prompt - defines the AI assistant's personality and capabilities
SYSTEM_PROMPT = """You are the Art Studio Companion, a friendly and knowledgeable AI assistant that helps artists manage their creative workflow. You have access to tools that let you:

1. **Pinterest Inspiration**: Search for art inspiration based on themes, styles, and subjects. Analyze the user's aesthetic preferences from their Pinterest boards.

2. **Supply Inventory**: Track the user's art supplies including paints, brushes, canvases, and papers. Know exact quantities, brands, and alert when supplies are running low.

3. **Portfolio Storehouse**: Manage the user's artwork portfolio with progress photos, descriptions, and completion status. Track the evolution from sketch to finished piece.

4. **Project Filesaver**: Create and save detailed project plans with materials lists, step-by-step instructions, and session notes.

Your personality:
- Encouraging and supportive of the user's artistic journey
- Knowledgeable about art techniques, materials, and color theory
- Practical and supply-aware - always consider what materials the user actually has
- Organized - help plan projects with actionable steps
- Memory-focused - remember the user's preferences, past projects, and artistic style

When a user describes a project idea:
1. First check their available supplies
2. Consider their style preferences from past conversations and Pinterest
3. Suggest a complete, actionable plan with specific materials they have
4. Note any supplies they might need to purchase
5. Offer technique tips relevant to their experience level

Always be specific about brands and quantities when discussing supplies (e.g., "You have 3/4 tube of Winsor & Newton Cadmium Yellow" not just "you have yellow paint").
"""

# Agent persona - additional context about the agent
AGENT_PERSONA = """I am the Art Studio Companion, your personal art studio manager. I help you:
- Plan art projects based on what supplies you actually have
- Track your inventory so you never run out mid-project
- Find inspiration that matches your aesthetic preferences
- Build and maintain your portfolio of artwork
- Remember your artistic journey and style evolution

I have persistent memory, so I remember our past conversations, your preferences, and your artistic history."""

# Human persona template
HUMAN_PERSONA = """The user is an artist who uses this companion to manage their art studio workflow. They may ask about:
- Project ideas and planning
- Supply inventory and shopping lists
- Inspiration and style suggestions
- Portfolio management
- Technique advice"""


class ArtStudioAgent:
    """Wrapper for the Letta agent with Art Studio tools."""

    def __init__(self):
        self.client = None
        self.agent_state = None
        self.agent_id = None

    def initialize(self):
        """Initialize the Letta client and agent."""
        # Create Letta client
        base_url = os.getenv("LETTA_BASE_URL", "http://localhost:8283")
        self.client = create_client(base_url=base_url)

        # Check for existing agent or create new one
        self.agent_id = self._get_or_create_agent()

    def _get_or_create_agent(self) -> str:
        """Get existing agent or create a new one."""
        agent_name = "art_studio_companion"

        # Try to find existing agent
        existing_agents = self.client.list_agents()
        for agent in existing_agents:
            if agent.name == agent_name:
                self.agent_state = agent
                return agent.id

        # Create new agent with tools
        tools = self._create_tools()

        # Configure memory
        memory = ChatMemory(
            human=HUMAN_PERSONA,
            persona=AGENT_PERSONA
        )

        # Create agent
        self.agent_state = self.client.create_agent(
            name=agent_name,
            system=SYSTEM_PROMPT,
            memory=memory,
            tools=[t.name for t in tools],
            llm_config=LLMConfig(
                model="gpt-4o-mini",  # Can be configured via env
                model_endpoint_type="openai",
                model_endpoint=os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1"),
                context_window=128000
            ),
            embedding_config=EmbeddingConfig(
                embedding_endpoint_type="openai",
                embedding_model="text-embedding-3-small",
                embedding_dim=1536
            )
        )

        return self.agent_state.id

    def _create_tools(self) -> list:
        """Create and register Letta tools from our MCP tools."""
        tools = []

        # Pinterest Inspiration Tools
        from app.tools.pinterest_inspiration import (
            get_pinterest_boards,
            search_pinterest_inspiration,
            analyze_style_preferences,
            save_style_preference
        )

        tools.extend([
            self.client.create_or_update_tool(get_pinterest_boards),
            self.client.create_or_update_tool(search_pinterest_inspiration),
            self.client.create_or_update_tool(analyze_style_preferences),
            self.client.create_or_update_tool(save_style_preference),
        ])

        # Supply Inventory Tools
        from app.tools.supply_inventory import (
            get_all_supplies,
            get_supply_by_id,
            add_supply,
            update_supply,
            get_low_stock_supplies,
            use_supply,
            search_supplies,
            get_supplies_for_project
        )

        tools.extend([
            self.client.create_or_update_tool(get_all_supplies),
            self.client.create_or_update_tool(get_supply_by_id),
            self.client.create_or_update_tool(add_supply),
            self.client.create_or_update_tool(update_supply),
            self.client.create_or_update_tool(get_low_stock_supplies),
            self.client.create_or_update_tool(use_supply),
            self.client.create_or_update_tool(search_supplies),
            self.client.create_or_update_tool(get_supplies_for_project),
        ])

        # Portfolio Tools
        from app.tools.portfolio_storehouse import (
            get_portfolio,
            get_portfolio_piece,
            add_portfolio_piece,
            update_portfolio_piece,
            add_progress_image,
            get_portfolio_stats
        )

        tools.extend([
            self.client.create_or_update_tool(get_portfolio),
            self.client.create_or_update_tool(get_portfolio_piece),
            self.client.create_or_update_tool(add_portfolio_piece),
            self.client.create_or_update_tool(update_portfolio_piece),
            self.client.create_or_update_tool(add_progress_image),
            self.client.create_or_update_tool(get_portfolio_stats),
        ])

        # Project Tools
        from app.tools.project_filesaver import (
            get_all_projects,
            get_project,
            create_project,
            update_project,
            save_project_to_file,
            generate_shopping_list,
            create_project_from_query,
            add_session_notes
        )

        tools.extend([
            self.client.create_or_update_tool(get_all_projects),
            self.client.create_or_update_tool(get_project),
            self.client.create_or_update_tool(create_project),
            self.client.create_or_update_tool(update_project),
            self.client.create_or_update_tool(save_project_to_file),
            self.client.create_or_update_tool(generate_shopping_list),
            self.client.create_or_update_tool(create_project_from_query),
            self.client.create_or_update_tool(add_session_notes),
        ])

        return tools

    def send_message(self, message: str) -> dict:
        """
        Send a message to the agent and get a response.

        Args:
            message: User's message

        Returns:
            Dictionary with agent response and any tool calls made.
        """
        if not self.client or not self.agent_id:
            self.initialize()

        try:
            response = self.client.send_message(
                agent_id=self.agent_id,
                message=message,
                role="user"
            )

            # Extract the response content
            messages = []
            tool_calls = []

            for msg in response.messages:
                if hasattr(msg, 'assistant_message') and msg.assistant_message:
                    messages.append(msg.assistant_message)
                if hasattr(msg, 'tool_call') and msg.tool_call:
                    tool_calls.append({
                        "name": msg.tool_call.name,
                        "arguments": msg.tool_call.arguments
                    })

            return {
                "success": True,
                "response": " ".join(messages) if messages else "I processed your request.",
                "tool_calls": tool_calls
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_memory_summary(self) -> dict:
        """Get a summary of the agent's memory."""
        if not self.client or not self.agent_id:
            return {"success": False, "error": "Agent not initialized"}

        try:
            memory = self.client.get_agent_memory(agent_id=self.agent_id)
            return {
                "success": True,
                "memory": {
                    "human": memory.human if hasattr(memory, 'human') else None,
                    "persona": memory.persona if hasattr(memory, 'persona') else None
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Singleton instance
_agent_instance: Optional[ArtStudioAgent] = None


def get_agent() -> ArtStudioAgent:
    """Get or create the singleton agent instance."""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = ArtStudioAgent()
        _agent_instance.initialize()
    return _agent_instance
