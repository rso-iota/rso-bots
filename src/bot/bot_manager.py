import asyncio
import logging
from typing import Dict, Optional
from uuid import UUID, uuid4

from .game_client import GameClient
from .strategy import BotStrategy
from src.config.settings import Settings

logger = logging.getLogger(__name__)

class BotInstance:
    def __init__(self, game_id: str, name: str, strategy: str = "random", host_name: str = "localhost", game_port: int = 8080):
        self.id = uuid4()
        self.name = name
        self.game_id = game_id
        self.strategy = strategy
        self.host_name = host_name
        self.game_port = game_port
        self.client = None
        self.task: Optional[asyncio.Task] = None
        
    async def start(self):
        """Start the bot instance"""
        self.client = GameClient(
            game_id=self.game_id,
            player_name=self.name,
            strategy=self.strategy,
            host_name=self.host_name,
            game_port=self.game_port,
            bot_id=self.id
        )
        self.task = asyncio.create_task(self._run())
        
    async def stop(self):
        """Stop the bot instance"""
        logger.info(f"Stopping bot {self.name}")
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

    async def _run(self):
        """Run the bot and handle its lifecycle"""
        logger.info(f"Bot {self.name} starting")
        try:
            await self.client.run()
        except Exception as e:
            logger.error(f"Bot {self.name} encountered an error: {e}")
        finally:
            # If we get here, either the bot died or encountered an error
            logger.info(f"Bot {self.name} finished running")

class BotManager:
    def __init__(self, settings: Settings):
        self.bots: Dict[UUID, BotInstance] = {}
        self.settings = settings
        
    async def create_bot(self, name: str, game_id: str, strategy: str = "random", host_name='localhost', game_port: int = 8080) -> UUID:
        """Create and start a new bot"""
        logger.info(f"Creating bot {name} for game {game_id}")
        bot = BotInstance(game_id, name, strategy, host_name, game_port)
        await bot.start()
        
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
            "game_id": bot.game_id,
            "alive": bot.client and bot.client.player_data and bot.client.player_data.get("alive", False)
        }
        
    def get_all_bots(self) -> list[dict]:
        """Get status of all bots"""
        return [
            {
                "id": bot.id,
                "name": bot.name,
                "game_id": bot.game_id,
                "alive": bot.client and bot.client.player_data and bot.client.player_data.get("alive", False)
            }
            for bot in self.bots.values()
        ]
