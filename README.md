# Agent Collaboration Platform

A distributed multi-agent system demonstrating asynchronous agent-to-agent communication with shared memory context using MCP (Memory Context Protocol).

**Maintained by:** Malaika Nasir

## Overview

This project showcases a modern architecture for building AI agent ecosystems where multiple specialized agents collaborate through message passing and shared memory, enabling complex workflows without tight coupling.

### Key Features

- **Agent-to-Agent Messaging** – Asynchronous, broker-based communication between agents
- **Shared Memory Context** – MCP Registry for centralized document storage
- **LLM Integration** – Groq LLM for intelligent text analysis
- **Web Frontend** – User-friendly interface for submitting tasks
- **Modular Architecture** – Independent, scalable services
- **Easy Deployment** – Docker Compose support for one-command setup

## Architecture

The system consists of 5 core services:

```
┌─────────────┐
│   Frontend  │ (Port 8000) - Web UI & Orchestration
└──────┬──────┘
       │
       ├──────────────────────────────┐
       │                              │
   ┌───▼────┐                    ┌────▼───┐
   │   MCP   │                    │ Broker  │
   │Registry │                    │Service  │
   └────▲────┘                    └────▲───┘
        │                             │
        │ (Read/Write)           (Send/Poll)
        │                             │
   ┌────┴──────────────────────────┬──┘
   │                               │
┌──▼──────────┐           ┌────────▼──┐
│  Researcher │           │  Analyst   │
│   Agent     │           │   Agent    │
│ (Port 7001) │           │ (Port 7002)│
└─────────────┘           └────────────┘
```

### Service Descriptions

| Service | Port | Purpose |
|---------|------|---------|
| **Frontend** | 8000 | Web UI for users to submit documents for analysis |
| **Broker** | 7003 | Message queue routing between agents |
| **MCP Registry** | 7000 | Centralized document/context storage |
| **Researcher** | 7001 | Creates documents and manages workflows |
| **Analyst** | 7002 | Analyzes documents using Groq LLM |

## Getting Started

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Groq API key (get one at [console.groq.com](https://console.groq.com))

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/agent-collaboration-platform.git
   cd agent-collaboration-platform
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```
   Then edit `.env` and add your Groq API key:
   ```
   GROQ_API_KEY=your_actual_api_key_here
   ```

### Running the Application

#### Option 1: Using Docker Compose (Recommended)

```bash
docker-compose up
```

Then visit: `http://localhost:8000`

#### Option 2: Running Services Manually

Open 5 terminal windows and run these commands:

**Terminal 1 - MCP Registry:**
```bash
uvicorn src.services.mcp_registry:app --port 7000 --reload
```

**Terminal 2 - Broker:**
```bash
uvicorn src.services.broker_service:app --port 7003 --reload
```

**Terminal 3 - Analyst Agent:**
```bash
uvicorn src.services.analyst_service:app --port 7002 --reload
```

**Terminal 4 - Researcher Agent:**
```bash
uvicorn src.services.researcher_service:app --port 7001 --reload
```

**Terminal 5 - Frontend:**
```bash
uvicorn src.services.frontend_service:app --port 8000 --reload
```

Once all services are running, visit: `http://localhost:8000`

### Usage

1. Open the web interface at `http://localhost:8000`
2. Enter text or a document in the input field
3. Click "Analyze"
4. The system will:
   - Store your document in the MCP Registry
   - Send it to the Analyst agent for processing
   - Use Groq LLM to extract KPIs and generate a summary
   - Return the analysis results to the frontend

## Project Structure

```
agent-collaboration-platform/
├── src/
│   ├── services/
│   │   ├── analyst_service.py      # LLM-powered analysis agent
│   │   ├── broker_service.py       # A2A message broker
│   │   ├── frontend_service.py     # Web UI & orchestration
│   │   ├── researcher_service.py   # Document creation agent
│   │   └── mcp_registry.py         # Shared memory context
│   └── __init__.py
├── tests/                          # Testing directory
├── docker-compose.yml              # Docker multi-container setup
├── Dockerfile                      # Container image
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment configuration template
├── .gitignore                      # Git exclusions
└── README.md                       # This file
```

## API Endpoints

### Frontend Service (Port 8000)
- `GET /` - Web UI
- `POST /analyze` - Submit document for analysis

### Broker Service (Port 7003)
- `POST /a2a/send` - Send A2A message
- `GET /a2a/poll/{receiver}` - Poll messages for receiver

### MCP Registry (Port 7000)
- `POST /mcp/resources/create` - Create/store resource
- `GET /mcp/resources/fetch/{rid}` - Fetch resource by ID

### Analyst Service (Port 7002)
- `GET /docs` - API documentation
- `GET /inbox` - View received messages
- `DELETE /inbox/clear` - Clear inbox

### Researcher Service (Port 7001)
- `GET /docs` - API documentation
- `POST /send-request` - Send analysis request

## Environment Variables

See `.env.example` for all available configuration options:

- `GROQ_API_KEY` - Your Groq API key
- `MCP_BASE` - MCP Registry base URL
- `MCP_REGISTRY_TOKEN` - Authentication token for MCP
- `BROKER_URL` - Broker service URL

## Development

### Running Tests

```bash
pytest
```

## Support

For issues, questions, or suggestions, please open an issue on GitHub.

## Authors

Created as a demonstration of modern multi-agent AI systems.
