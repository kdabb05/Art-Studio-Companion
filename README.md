# Art-Studio-
**Art Studio Companion Project Overview**

The Art Studio Companion is a web-based AI assistant that acts as your personal art studio manager—helping you plan projects, discover inspiration from your social media tastes, track supplies down to specific brands and quantities, and maintain a private portfolio of your work. Built as an LLM agentic application using OpenRouter's ReAct loop, it powers a conversational interface where you describe ideas like "watercolor sunflower landscape under $30" and receive complete, supply-aware project plans.

## Agent Capabilities
The core ReAct agent reasons step-by-step through your requests:
- **Interprets** natural language goals ("I want a landscape painting using what I have")
- **Calls MCP tools** strategically to gather data (Pinterest boards, supply levels, portfolio pieces)
- **Observes results** and iterates ("Pinterest shows you like loose brushwork; you have 3/4 tube Winsor yellow")
- **Delivers final answer** with actionable project steps, shopping lists, and style tips personalized to your inventory and aesthetic
- **Remembers context** across multi-turn conversations and app restarts

## AI & Tools
- **Uses OpenRouter API** for LLM access with flexible model selection
- **API key stored securely** using a `.env` file (never committed to GitHub)
- **Modular backend design** separating chat handling, MCP tools, and memory persistence for clean separation of concerns

## MCP Tools (4 Total)
Exposed via standardized MCP server endpoints for agent access:
- **Pinterest Inspiration**: Asks for your username → fetches boards/hashtags → returns curated images matching your project theme
- **Supply Inventory Manager**: Tracks exact supplies ("Winsor watercolor 3/4 full, Princeton #6 brush"); **analyzes uploaded photos** of your collection to auto-generate/update inventory lists
- **Portfolio Storehouse**: Private storage/retrieval of your artwork with progress photos, descriptions, and completion status
- **Project Filesaver**: Saves detailed project plans, sketches, material lists, and session notes to local files

## Long-Term Memory
SQLite database persists:
- **Supply snapshots** over time (quantity used per project)
- **Style preferences** inferred from Pinterest patterns and chat history
- **Portfolio evolution** (sketches → WIPs → finished pieces)
- **Project outcomes** (what worked, what to buy next time)

## User Interface
Clean web app (Flask + HTML/JS) with:
- **Main chat window** for natural conversation with the agent
- **Sidebar panels**:
  - Current supply status (color-coded: green=plenty, yellow=low, red=empty)
  - Saved projects list (click to resume)
  - Portfolio gallery thumbnails
- **Quick actions**: "Scan supplies" (photo upload), "New project," "Show low stock"
- **Persistent state**: Remembers your supplies/portfolio between browser sessions

This creates a genuine studio workflow companion that knows your exact materials, aesthetic preferences from Pinterest, and artistic progress—making every project suggestion immediately executable with professional-grade technical architecture.
