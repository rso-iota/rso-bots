import asyncio
import grpc
from concurrent import futures
import logging
import threading

from .bot.service import BotServiceServicer
from .proto import bot_pb2_grpc
from src.config.settings import Settings

settings = Settings()

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

def run_grpc_server(loop):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    servicer = BotServiceServicer()
    servicer.loop = loop
    bot_pb2_grpc.add_BotServiceServicer_to_server(servicer, server)
    server.add_insecure_port(f'[::]:{settings.grpc_port}')
    server.start()
    logger.info(f"Bot service started on port {settings.grpc_port}")
    server.wait_for_termination()

def serve():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    server_thread = threading.Thread(target=run_grpc_server, args=(loop,))
    server_thread.start()
    
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()

if __name__ == '__main__':
    serve()
