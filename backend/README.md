# 🎬 Director Backend

## 📋 Overview

The Director Backend is a Python-based server application that powers the Director project. It provides a robust framework for managing video processing tasks, agent-based operations, and communication with the frontend.

## 🚀 Getting Started

### 🐳 Running with Docker

To run the backend using Docker:

1. Build the Docker image:
   ```bash
   docker build -t director-backend .
   ```

2. Run the container:
   ```bash
   docker run -p 8000:8000 director-backend
   ```

The server will be available at `http://localhost:8000`.

## 🏗️ Core Components

### 🧠 Reasoning Engine (`director/core/reasoning.py`)

The Reasoning Engine is the central component that orchestrates agents, interprets user input, and manages the conversation flow. It uses LLMs for natural language understanding and agent orchestration.

### 📡 Session Management (`director/core/session.py`)

The Session class manages user sessions, conversations, and message handling. It provides methods for creating, retrieving, and managing session data.

### 💬 Message Classes

- `BaseMessage`: The foundation for all message types.
- `InputMessage`: Represents user input.
- `OutputMessage`: Represents system output, including agent responses.
- `ContextMessage`: Manages conversation context for the reasoning engine.

## 🤖 Agents

Agents are modular components that perform specific tasks. The `BaseAgent` class (`director/agents/base.py`) provides a foundation for creating custom agents. Sample agents like `SampleAgent` (`director/agents/sample.py`) demonstrate how to implement agent functionality.

## 🗄️ Database

The project uses a database abstraction layer (`director/db/base.py`) that can be implemented for different database systems. The current implementation uses SQLite (`director/db/sqlite/`).

## 🚪 Entrypoint

The main entry point for the backend is the Flask server (`director/entrypoint/api/server.py`). It sets up routes, WebSocket connections, and initializes the necessary components.

## 🔌 Socket Communication

The backend uses Flask-SocketIO for real-time communication with the frontend. Socket events are used to send and receive messages, updates, and other real-time data.

## 🛠️ Tools

The `VideoDBTool` (`director/tools/videodb_tool.py`) provides an interface for interacting with the VideoDB API, allowing operations like video upload, search, and manipulation.

## 🧠 LLM Integration

The `BaseLLM` class (`director/llm/base.py`) provides an abstraction for integrating different Language Model providers. The current implementation supports OpenAI (`director/llm/openai.py`) and EvoLink (`director/llm/evolink.py`).

## 📦 Dependencies

Main dependencies include:
- Flask
- Flask-SocketIO
- OpenAI
- Pydantic
- VideoDB Python Client

For a full list of dependencies, see `requirements.txt`.

## 🔧 Configuration

Environment variables and configuration settings can be managed using `.env` files or system environment variables. Key configurations include API keys, database settings, and LLM parameters.

## 🚀 Development

To set up the development environment:

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  
   ```

2. Install dependencies for development:
   ```bash
   pip install -r requirements.txt
   ```
   ```bash
   pip install -r requirements-dev.txt
   ```

3. Run the development server:
   ```bash
   python director/entrypoint/api/server.py
   ```

### Using Make
1. Init the database from make file of the root of project

```bash
make init-sqlite-db
```

2. Install the dependencies:

```bash
make install
```

* Run Development server:

```bash
make run
```

## 📚 Further Documentation

For more detailed information about specific components, please refer to the MkDocs documentation.
