# RSO Bot Service

A service that manages multiple game bots for the RSO game system. Each bot is an independent player that can join games and play autonomously using configurable strategies.

## Features

- gRPC API for bot management
- Manages multiple bot instances concurrently
- Configurable bot strategies and difficulty levels
- WebSocket communication with game server
- Automatic reconnection handling
- Environment-based configuration
- Health checks (liveness and readiness probes)

## Installation

### Requirements

- Python 3.11 or higher
- uv (modern Python package manager)
- Protocol Buffers compiler (protoc)

### Setup

1. Create a virtual environment:
```bash
uv venv
```

2. Install dependencies:
```bash
uv pip install -e .
```

3. Copy the example env file and configure:
```bash
cp .env.example .env
```

Required environment variables:
- GAME_SERVER_URL: WebSocket URL of the game server
- GRPC_PORT: Port for the gRPC server (default: 50051)
- GAME_PORT: Port for the game server (default: 8080)
- LOG_LEVEL: Logging level (default: INFO)

### Running

Start the service:
```bash
python src/main.py
```

### Docker

Build:
```bash
docker build -t rso-bots .
```

Run:
```bash
docker run -p 50051:50051 -p 8080:8080 --env-file .env rso-bots
```

## API Reference

The service exposes a gRPC API with the following endpoints:

### CreateBot

Creates a new bot instance.

```protobuf
rpc CreateBot(CreateBotRequest) returns (CreateBotResponse)

message CreateBotRequest {
    string bot_id = 1;
    Bot bot = 2;
    string access_token = 3;
    string hostname = 4;
}

message Bot {
    string game_id = 1;
    string difficulty = 2;  // easy, medium, hard
    optional string strategy = 3;
}

message CreateBotResponse {
    string bot_id = 1;
    string status = 2;
}
```

### DeleteBot

Removes a bot instance.

```protobuf
rpc DeleteBot(DeleteBotRequest) returns (Empty)

message DeleteBotRequest {
    string bot_id = 1;
}
```

### GetBot

Retrieves bot information.

```protobuf
rpc GetBot(GetBotRequest) returns (Bot)

message GetBotRequest {
    string bot_id = 1;
}
```

### ListBots

Lists all active bots.

```protobuf
rpc ListBots(Empty) returns (ListBotsResponse)

message ListBotsResponse {
    map<string, Bot> bots = 1;
}
```

### Health Checks

The service also exposes HTTP health check endpoints:

```http
GET /health/live
```
Liveness probe - returns service status.

```http
GET /health/ready
```
Readiness probe - verifies service is accepting requests.

## Errors

The API uses standard gRPC status codes:

- ALREADY_EXISTS: Bot with given ID already exists and is active
- NOT_FOUND: Bot with given ID does not exist
- INVALID_ARGUMENT: Invalid request parameters
- UNAVAILABLE: Game server connection failed
- INTERNAL: Unexpected server error

## Architecture

Core components:

- BotService: gRPC server implementing the bot management API
- BotManager: Manages bot lifecycle and state
- GameClient: Handles WebSocket communication with game server
- BotStrategy: Implements bot behavior and decision making
- Health checks: Monitor service health via HTTP endpoints

Each bot runs independently with:
- Message handling for WebSocket communication
- Strategy execution for game logic
- Automatic reconnection on disconnection