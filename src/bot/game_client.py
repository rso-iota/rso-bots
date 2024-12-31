import json
import logging
import asyncio
import websockets
from typing import Optional

class GameClient:
    def __init__(self, server_url: str):
        self.server_url = server_url
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.game_state = None
        
    async def connect(self, game_id: str, bot_name: str):
        """Connect to a specific game"""
        url = f"{self.server_url}/game/{game_id}"
        self.websocket = await websockets.connect(url)
        
        # Send join message
        join_message = {
            "type": "join",
            "data": {
                "playerName": bot_name
            }
        }
        await self.websocket.send(json.dumps(join_message))
        
    async def move(self, dx: float, dy: float):
        """Send move command"""
        if self.websocket:
            move_message = {
                "type": "move",
                "data": {
                    "x": dx,
                    "y": dy
                }
            }
            await self.websocket.send(json.dumps(move_message))
    
    async def handle_messages(self):
        """Handle incoming game messages"""
        try:
            while True:
                message = await self.websocket.recv()
                data = json.loads(message)
                
                if data["type"] == "gameState":
                    self.game_state = data["data"]
                elif data["type"] == "update":
                    # Update game state with new information
                    self.update_game_state(data["data"])
                    
        except websockets.ConnectionClosed:
            logging.error("Connection to game server closed")
            
    def update_game_state(self, update_data):
        """Update internal game state with new data"""
        if not self.game_state:
            return
            
        # Update players
        if "players" in update_data:
            for player_update in update_data["players"]:
                for player in self.game_state["players"]:
                    if player["name"] == player_update["playerName"]:
                        player.update(player_update)
                        
        # Update food
        if "food" in update_data:
            self.game_state["food"] = update_data["food"]