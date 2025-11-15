# Atlassian Agents Project

This project provides a framework for building and deploying AI agents that can interact with Atlassian products like Confluence. It includes a backend for agent logic and a frontend UI for interaction.

## Features

- **Modular Agent Framework:** Easily create and integrate new AI agents.
- **Confluence Agent:** An example agent demonstrating interaction with Confluence.
- **Web-based UI:** A user-friendly interface for interacting with the agents.
- **Dockerized Deployment:** Simple deployment using Docker and Docker Compose.

## Project Structure

```
.github/                 # GitHub workflows
app/                     # Backend Python application
├── agents/              # AI agent implementations
│   ├── confluence_agent.py # Confluence-specific agent
│   └── universal_assistant.py # Generic assistant agent
├── core/                # Core functionalities (config, logging, constants)
├── prompts/             # Agent prompts
├── schemas/             # Data schemas
├── tests/               # Backend tests
└── utils/               # Backend utilities
caddy/                   # Caddy server configuration
deep-agents-ui/          # Next.js frontend application
├── public/              # Static assets
├── src/                 # Frontend source code
│   ├── app/             # Next.js app directory (pages, components, hooks)
│   └── lib/             # Frontend libraries and utilities
docs/                    # Documentation files
├── CONFLUENCE_AGENT_GUIDE.md
└── CONFLUENCE_AGENT_QUICK_REFERENCE.md
docker-compose.yml       # Docker Compose setup for all services
main.py                  # Backend application entry point
pyproject.toml           # Poetry project configuration
```

## Setup

To get the project up and running, follow these steps:

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/atlassian-agents.git
    cd atlassian-agents
    ```

2.  **Start with Docker Compose:**
    Ensure you have Docker and Docker Compose installed. Then, from the project root, run:
    ```bash
    docker-compose up --build
    ```
    This will build the Docker images and start all services, including the backend agent server and the frontend UI.

3.  **Access the UI:**
    Once the services are up, the frontend UI should be accessible at `http://localhost:3000` (or the port configured in `docker-compose.yml`).

4.  **Configure Atlassian API (Optional):**
    If you plan to use agents that interact with Atlassian products, you'll need to provide your Atlassian API credentials. Refer to the `app/core/config.py` for environment variables and configuration details.

## Usage

1.  **Interact via UI:** Open your browser to `http://localhost:3000` (or your configured UI port). You can select an agent and start interacting with it through the chat interface.

2.  **Confluence Agent:** If the Confluence agent is enabled and configured, you can ask it questions related to your Confluence spaces, summarize pages, or even request it to draft content.

    Refer to `docs/CONFLUENCE_AGENT_GUIDE.md` and `docs/CONFLUENCE_AGENT_QUICK_REFERENCE.md` for more details on how to use the Confluence agent effectively.

## Technologies Used

**Backend:**

-   Python
-   FastAPI
-   LangChain / LangGraph (for agent orchestration)
-   Poetry (dependency management)

**Frontend:**

-   Next.js
-   React
-   TypeScript
-   Tailwind CSS (for styling)

**Deployment:**

-   Docker
-   Docker Compose
-   Caddy (reverse proxy)
