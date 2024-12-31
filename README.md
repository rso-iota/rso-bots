# RSO Bot Service

A service that manages multiple game bots for the RSO game.

## Features

- Manages multiple bot instances concurrently
- Configurable bot strategies
- WebSocket communication with game server
- Environment-based configuration

## Development

### Requirements

- Python 3.11 or higher
- uv (modern Python package manager)

### Setup

1. Create a virtual environment:
```bash
uv venv
```

2. Install dependencies:
```bash
uv pip install -e .
```

3. Copy the example env file and configure it:
```bash
cp .env.example .env
```

Edit the .env file with your configuration:
- GAME_SERVER_URL: WebSocket URL of the game server
- GAME_ID: ID of the game to connect to
- INITIAL_BOTS: Number of bots to start with
- BOT_NAME_PREFIX: Prefix for bot names

### Running

```bash
python src/main.py
```

### Docker

Build the image:
```bash
docker build -t rso-bots .
```

Run with Docker:
```bash
docker run --env-file .env rso-bots
```

## Architecture

The service consists of several components:

- GameClient: Handles WebSocket communication with the game server
- BotStrategy: Implements bot behavior and decision making
- BotManager: Manages multiple bot instances
- BotInstance: Individual bot runtime with its own WebSocket connection

Each bot runs independently with:
- Message handling task for WebSocket communication
- Strategy execution task for game logic
- Automatic reconnection on disconnection