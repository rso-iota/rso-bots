import asyncio
import logging
from concurrent import futures
from typing import Dict
import grpc
import uuid

from src.bot.game_client import GameClient
from src.proto import bot_pb2
from src.proto import bot_pb2_grpc

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BotManager:
    def __init__(self):
        self._bots: Dict[str, bot_pb2.Bot] = {}
        self._game_clients: Dict[str, GameClient] = {}
        self._tasks: Dict[str, asyncio.Task] = {}
    
    async def add_bot(self, bot_id: str, bot: bot_pb2.Bot) -> None:
        if bot_id in self._bots:
            raise ValueError(f"Bot {bot_id} already exists")
        
        self._bots[bot_id] = bot
        client = GameClient(
            game_id=bot.game_id,
            player_name=f"Bot-{bot_id[:6]}",
            strategy=bot.strategy if bot.strategy else "greedy"
        )
        self._game_clients[bot_id] = client
        
        self._tasks[bot_id] = asyncio.create_task(client.run())
        logger.info(f"Added bot {bot_id} to game {bot.game_id}")

    async def remove_bot(self, bot_id: str) -> None:
        if bot_id not in self._bots:
            raise ValueError(f"Bot {bot_id} does not exist")
        
        if bot_id in self._tasks:
            self._tasks[bot_id].cancel()
            try:
                await self._tasks[bot_id]
            except asyncio.CancelledError:
                pass
            del self._tasks[bot_id]
        
        if bot_id in self._game_clients:
            client = self._game_clients[bot_id]
            if client.ws:
                await client.ws.close()
            del self._game_clients[bot_id]
        
        del self._bots[bot_id]
        logger.info(f"Removed bot {bot_id}")

class BotServiceServicer(bot_pb2_grpc.BotServiceServicer):
    def __init__(self):
        self.bot_manager = BotManager()
        self.loop = None

    def CreateBot(self, request, context):
        try:
            future = asyncio.run_coroutine_threadsafe(
                self.bot_manager.add_bot(request.bot_id, request.bot),
                self.loop
            )
            future.result(timeout=10)  # 10 second timeout
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
            context.set_details(str(e))
            return bot_pb2.CreateBotResponse()

    def DeleteBot(self, request, context):
        try:
            future = asyncio.run_coroutine_threadsafe(
                self.bot_manager.remove_bot(request.bot_id),
                self.loop
            )
            future.result(timeout=10)
            return bot_pb2.Empty()
        except ValueError as e:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(str(e))
            return bot_pb2.Empty()
        except Exception as e:
            logger.error(f"Error deleting bot: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return bot_pb2.Empty()

    def GetBot(self, request, context):
        bot_id = request.bot_id
        if bot_id not in self.bot_manager._bots:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Bot {bot_id} not found")
            return bot_pb2.Bot()
        return self.bot_manager._bots[bot_id]

    def ListBots(self, request, context):
        return bot_pb2.ListBotsResponse(bots=self.bot_manager._bots)