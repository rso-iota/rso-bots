import asyncio
import json
import logging
import websockets
from typing import Optional
import math
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GameClient:
    """Client for connecting to and interacting with the game server."""

    def __init__(
        self,
        game_id: str,
        player_name: str,
        strategy: str = "random",
        game_port: int = 8080,
    ):
        self.game_id = game_id
        self.player_name = player_name
        self.strategy = strategy
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.connected = False
        self.player_data = None
        self.game_state = None
        self.game_port = game_port
        self.target_food = None

    async def connect(self):
        """Connect to the game server."""
        try:
            logger.info(f"Connecting to game {self.game_id}")
            self.ws = await websockets.connect(
                f"ws://localhost:{self.game_port}/connect/{self.game_id}"
            )
            self.connected = True
            logger.info(f"Connected to game {self.game_id}")

            # Send join message
            join_msg = {"type": "join", "data": {"playerName": self.player_name}}
            await self.send_message(join_msg)

            return True
        except Exception as e:
            logger.error(f"Failed to connect to game: {e}")
            return False

    async def send_message(self, message: dict):
        """Send a message to the game server."""
        if not self.ws:
            return
        try:
            await self.ws.send(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            self.connected = False

    async def handle_messages(self):
        """Handle incoming messages from the game server."""
        if not self.ws:
            return

        try:
            while True:
                message = await self.ws.recv()
                data = json.loads(message)

                if data["type"] == "gameState":
                    self.game_state = data["data"]
                    # Find our player
                    for player in self.game_state["players"]:
                        if player["playerName"] == self.player_name:
                            self.player_data = player
                            break

                elif data["type"] == "update":
                    if "players" in data["data"]:
                        for player in data["data"]["players"]:
                            if player["playerName"] == self.player_name:
                                self.player_data = player
                                break
                    if "food" in data["data"]:
                        self.game_state["food"] = [
                            f
                            for f in self.game_state["food"]
                            if f["index"]
                            not in [upd_f["index"] for upd_f in data["data"]["food"]]
                        ] + data["data"]["food"]

        except websockets.exceptions.ConnectionClosed:
            logger.info("Connection closed")
            self.connected = False
        except Exception as e:
            logger.error(f"Error handling messages: {e}")
            self.connected = False

    def calculate_move(self) -> tuple[float, float]:
        """Calculate the next move based on the current game state."""
        if not self.player_data or not self.player_data["alive"]:
            return 0, 0

        if self.strategy == "random":
            # Random movement
            angle = random.random() * 2 * math.pi
            return math.cos(angle), math.sin(angle)

        elif self.strategy == "greedy":
            # Find closest food that we can eat
            closest_food = None
            min_distance = float("inf")

            for food in self.game_state["food"]:
                dx = food["circle"]["x"] - self.player_data["circle"]["x"]
                dy = food["circle"]["y"] - self.player_data["circle"]["y"]
                distance = math.sqrt(dx * dx + dy * dy)

                if distance < min_distance:
                    min_distance = distance
                    closest_food = food

            if closest_food:
                dx = closest_food["circle"]["x"] - self.player_data["circle"]["x"]
                dy = closest_food["circle"]["y"] - self.player_data["circle"]["y"]
                magnitude = math.sqrt(dx * dx + dy * dy)
                if magnitude == 0:
                    return 0, 0
                return dx / magnitude, dy / magnitude

        return 0, 0

    async def game_loop(self):
        """Main game loop for the bot."""
        if not self.ws:
            return

        try:
            while self.connected:
                if self.player_data and self.game_state:
                    x, y = self.calculate_move()
                    move_msg = {"type": "move", "data": {"x": x, "y": y}}
                    await self.send_message(move_msg)
                await asyncio.sleep(0.03)  # 30ms delay to match server tick rate
        except Exception as e:
            logger.error(f"Error in game loop: {e}")
            self.connected = False

    async def run(self):
        """Run the game client."""
        if not await self.connect():
            return

        try:
            # Run message handler and game loop concurrently
            await asyncio.gather(self.handle_messages(), self.game_loop())
        finally:
            if self.ws:
                await self.ws.close()
