import grpc
from concurrent import futures
import logging

from .bot.service import BotServiceServicer
from .proto import bot_pb2_grpc

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def serve():
    """Start the gRPC server."""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    bot_pb2_grpc.add_BotServiceServicer_to_server(
        BotServiceServicer(), server
    )
    server.add_insecure_port('[::]:50051')
    server.start()
    logger.info("Bot service started on port 50051")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()