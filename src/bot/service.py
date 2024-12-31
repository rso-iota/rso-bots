import asyncio
import logging
from concurrent import futures
from typing import Dict
import grpc

# Use absolute imports
import proto.bot_pb2 as bot_pb2
import proto.bot_pb2_grpc as bot_pb2_grpc

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BotManager:
    """Manages bot lifecycle and connections."""
    def __init__(self):
        self._bots: Dict[str, bot_pb2.Bot] = {}
        self._tasks: Dict[str, asyncio.Task] = {}
    
    async def add_bot(self, bot_id: str, bot: bot_pb2.Bot) -> None:
        """Add a new bot to the game."""
        if bot_id in self._bots:
            raise ValueError(f"Bot {bot_id} already exists")
        
        self._bots[bot_id] = bot
        # Create an asyncio task for the bot
        loop = asyncio.get_event_loop()
        self._tasks[bot_id] = loop.create_task(self._run_bot(bot_id, bot))
        logger.info(f"Added bot {bot_id} to game {bot.game_id}")

    async def remove_bot(self, bot_id: str) -> None:
        """Remove a bot from the game."""
        if bot_id not in self._bots:
            raise ValueError(f"Bot {bot_id} does not exist")
        
        # Cancel the bot's task if it exists
        if bot_id in self._tasks:
            self._tasks[bot_id].cancel()
            try:
                await self._tasks[bot_id]
            except asyncio.CancelledError:
                pass
            del self._tasks[bot_id]
        
        del self._bots[bot_id]
        logger.info(f"Removed bot {bot_id}")

    async def _run_bot(self, bot_id: str, bot: bot_pb2.Bot) -> None:
        """Run the bot's game loop."""
        try:
            while True:
                # Here you would implement the actual bot behavior
                await asyncio.sleep(1)  # Placeholder for actual game logic
        except asyncio.CancelledError:
            logger.info(f"Bot {bot_id} task cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in bot {bot_id}: {e}")
            raise

class BotServiceServicer(bot_pb2_grpc.BotServiceServicer):
    """gRPC service implementation for bot management."""
    
    def __init__(self):
        self.bot_manager = BotManager()
        self.loop = asyncio.get_event_loop()

    def CreateBot(self, request, context):
        """Create a new bot with the specified configuration."""
        try:
            self.loop.run_until_complete(
                self.bot_manager.add_bot(request.bot_id, request.bot)
            )
            return bot_pb2.CreateBotResponse(
                bot_id=request.bot_id,
                status="created"
            )
        except ValueError as e:
            context.set_code(grpc.StatusCode.ALREADY_EXISTS)
            context.set_details(str(e))
            return bot_pb2.CreateBotResponse()
        except Exception as e:
            logger.error(f"Error creating bot: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Internal server error")
            return bot_pb2.CreateBotResponse()

    def DeleteBot(self, request, context):
        """Delete an existing bot."""
        try:
            self.loop.run_until_complete(
                self.bot_manager.remove_bot(request.bot_id)
            )
            return bot_pb2.Empty()
        except ValueError as e:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(str(e))
            return bot_pb2.Empty()
        except Exception as e:
            logger.error(f"Error deleting bot: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details("Internal server error")
            return bot_pb2.Empty()

    def GetBot(self, request, context):
        """Get information about a specific bot."""
        bot_id = request.bot_id
        if bot_id not in self.bot_manager._bots:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Bot {bot_id} not found")
            return bot_pb2.Bot()
        return self.bot_manager._bots[bot_id]

    def ListBots(self, request, context):
        """List all active bots."""
        return bot_pb2.ListBotsResponse(bots=self.bot_manager._bots)