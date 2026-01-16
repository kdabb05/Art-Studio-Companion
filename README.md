# Art Studio Companion

A web-based AI assistant that acts as your personal art studio manager—helping you plan projects, discover inspiration, track supplies down to specific brands and quantities, and maintain a private portfolio of your work.

Built with **Letta** for stateful agent memory, **Flask** for the web backend, and **SQLite** for persistent storage.

## Features

### Stateful AI Agent (Powered by Letta)
- **Persistent Memory**: Remembers your supplies, preferences, and project history across sessions
- **Natural Conversation**: Describe ideas like "watercolor sunflower landscape under $30" and receive complete, supply-aware project plans
- **Context Awareness**: Builds understanding of your artistic style over time

### MCP Tools (4 Total)
| Tool | Description |
|------|-------------|
| **Pinterest Inspiration** | Fetches boards/hashtags and returns curated images matching your project theme |
| **Supply Inventory Manager** | Tracks exact supplies with quantities and brands; alerts when running low |
| **Portfolio Storehouse** | Private storage of your artwork with progress photos and completion status |
| **Project Filesaver** | Saves detailed project plans, material lists, and session notes |

### Web Interface
- **Chat Window**: Natural conversation with the AI agent
- **Supply Status Sidebar**: Color-coded inventory (green=plenty, yellow=low, red=empty)
- **Projects Panel**: View and resume saved projects
- **Portfolio Gallery**: Thumbnail view of your artwork
- **Quick Actions**: Scan supplies, new project, show low stock, get inspiration

---

## Installation

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Letta server (for the stateful agent)

### Step 1: Clone the Repository

```bash
git clone https://github.com/liamstar97/cofi26-Art-Studio-Companion.git
cd cofi26-Art-Studio-Companion
```

### Step 2: Create Virtual Environment (Recommended)

```bash
python -m venv venv

# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# Required: OpenAI API Key (for Letta's LLM)
OPENAI_API_KEY=your_openai_api_key_here

# Letta Configuration
LETTA_BASE_URL=http://localhost:8283

# Optional: Pinterest API (for real Pinterest data)
PINTEREST_ACCESS_TOKEN=your_pinterest_token_here

# Flask Configuration
FLASK_SECRET_KEY=your_secret_key_here
FLASK_DEBUG=true
```

### Step 5: Start the Letta Server

In a separate terminal window:

```bash
# Install Letta if not already installed
pip install letta

# Start the Letta server
letta server
```

The Letta server will start on `http://localhost:8283`.

### Step 6: Run the Application

```bash
python run.py
```

The application will be available at `http://localhost:5000`.

---

## Usage

### Getting Started

1. Open `http://localhost:5000` in your browser
2. The AI assistant will greet you and explain its capabilities
3. Start by adding some supplies to your inventory or describing a project idea

### Example Conversations

**Planning a project:**
```
"I want to paint a watercolor landscape with what I have"
```

**Adding supplies:**
```
"Add to my inventory: Winsor & Newton Cadmium Yellow, half tube remaining"
```

**Checking inventory:**
```
"What supplies am I running low on?"
```

**Getting inspiration:**
```
"Show me some inspiration for botanical watercolor paintings"
```

### Quick Actions

- **Scan Supplies**: Upload a photo of your art supplies to add them to inventory
- **New Project**: Start planning a new art project with AI assistance
- **Show Low Stock**: View supplies that need restocking
- **Get Inspiration**: Get AI-curated inspiration for your next project

---

## Project Structure

```
art-studio-companion/
├── app/
│   ├── __init__.py           # Flask app factory
│   ├── agent.py              # Letta agent configuration
│   ├── routes.py             # API endpoints
│   ├── models/
│   │   ├── __init__.py
│   │   └── database.py       # SQLite models
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── pinterest_inspiration.py
│   │   ├── supply_inventory.py
│   │   ├── portfolio_storehouse.py
│   │   └── project_filesaver.py
│   ├── templates/
│   │   └── index.html        # Main web interface
│   └── static/
│       ├── css/
│       │   └── style.css
│       └── js/
│           └── app.js
├── data/
│   ├── portfolio/            # Uploaded artwork images
│   ├── projects/             # Saved project files
│   ├── supplies/             # Supply-related files
│   └── uploads/              # Temporary uploads
├── requirements.txt
├── run.py                    # Application entry point
├── .env.example              # Environment template
└── README.md
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat` | POST | Send message to AI agent |
| `/api/supplies` | GET | Get all supplies |
| `/api/supplies` | POST | Add new supply |
| `/api/supplies/low-stock` | GET | Get low stock items |
| `/api/supplies/scan` | POST | Upload supply photo |
| `/api/projects` | GET | Get all projects |
| `/api/projects/suggest` | POST | Get project suggestion |
| `/api/portfolio` | GET | Get portfolio pieces |
| `/api/portfolio/stats` | GET | Get portfolio statistics |
| `/api/portfolio/upload` | POST | Upload artwork image |
| `/api/dashboard` | GET | Get dashboard summary |

---

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | OpenAI API key for Letta's LLM |
| `LETTA_BASE_URL` | No | Letta server URL (default: `http://localhost:8283`) |
| `PINTEREST_ACCESS_TOKEN` | No | Pinterest API token for real data |
| `FLASK_SECRET_KEY` | No | Flask session secret key |
| `FLASK_DEBUG` | No | Enable debug mode (default: `true`) |
| `FLASK_HOST` | No | Server host (default: `0.0.0.0`) |
| `FLASK_PORT` | No | Server port (default: `5000`) |
| `DATABASE_URL` | No | Database URL (default: `sqlite:///data/art_studio.db`) |

---

## Troubleshooting

### "Could not connect to Letta server"
- Ensure the Letta server is running: `letta server`
- Check that `LETTA_BASE_URL` matches the server address

### "API key not configured"
- Make sure your `.env` file exists and contains valid API keys
- Restart the application after updating `.env`

### Database errors
- The database is automatically created on first run
- To reset, delete `data/art_studio.db` and restart

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit changes: `git commit -m "Add your feature"`
4. Push to branch: `git push origin feature/your-feature`
5. Open a Pull Request

---

## License

This project is open source and available under the MIT License.

---

## Acknowledgments

- [Letta](https://github.com/letta-ai/letta) - Stateful LLM agent framework
- [Flask](https://flask.palletsprojects.com/) - Python web framework
- [SQLAlchemy](https://www.sqlalchemy.org/) - Database ORM
