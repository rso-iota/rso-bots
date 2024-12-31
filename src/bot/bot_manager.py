import asyncio
import logging
from typing import Dict, Optional
from uuid import UUID, uuid4

from .game_client import GameClient
from .strategy import BotStrategy

logger = logging.getLogger(__name__)

class BotInstance:
    def __init__(self, client: GameClient, strategy: BotStrategy, name: str):
        self.id = uuid4()
        self.client = client
        self.strategy = strategy
        self.name = name
        self.task: Optional[asyncio.Task] = None
        
    async def start(self, game_id: str):
        """Start the bot instance"""
        await self.client.connect(game_id, self.name)
        # Create two tasks: one for receiving messages, one for bot logic
        self.message_task = asyncio.create_task(self.client.handle_messages())
        self.strategy_task = asyncio.create_task(self.run_strategy())
        
    async def stop(self):
        """Stop the bot instance"""
        if self.message_task:
            self.message_task.cancel()
        if self.strategy_task:
            self.strategy_task.cancel()
        if self.client.websocket:
            await self.client.websocket.close()
            
    async def run_strategy(self):
        """Run the bot's strategy loop"""
        try:
            while True:
                if self.client.game_state:
                    dx, dy = self.strategy.calculate_move(
                        self.client.game_state, 
                        self.name
                    )
                    await self.client.move(dx, dy)
                await asyncio.sleep(0.1)
        except Exception as e:
            logger.error(f"Error in bot {self.name} strategy: {e}")

class BotManager:
    def __init__(self, server_url: str):
        self.server_url = server_url
        self.bots: Dict[UUID, BotInstance] = {}
        
    async def create_bot(self, name: str, game_id: str, strategy_type: str = "basic") -> UUID:
        """Create and start a new bot"""
        client = GameClient(self.server_url)
        strategy = BotStrategy()  # You could have different strategy types
        
        bot = BotInstance(client, strategy, name)
        await bot.start(game_id)
        
        self.bots[bot.id] = bot
        return bot.id
        
    async def remove_bot(self, bot_id: UUID) -> bool:
        """Remove a bot"""
        if bot_id not in self.bots:
            return False
            
        bot = self.bots[bot_id]
        await bot.stop()
        del self.bots[bot_id]
        return True
        
    def get_bot_status(self, bot_id: UUID) -> Optional[dict]:
        """Get status of a specific bot"""
        if bot_id not in self.bots:
            return None
            
        bot = self.bots[bot_id]
        return {
            "id": bot.id,
            "name": bot.name,
            "game_state": bot.client.game_state
        }
        
    def get_all_bots(self) -> list[dict]:
        """Get status of all bots"""
        return [
            {
                "id": bot.id,
                "name": bot.name,
                "alive": bot.client.game_state is not None
            }
            for bot in self.bots.values()
        ]