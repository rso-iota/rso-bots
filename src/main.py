import asyncio
import grpc
from concurrent import futures
import logging
import threading
import uvicorn
from fastapi import FastAPI, status
from datetime import datetime
from typing import Dict

from .bot.service import BotServiceServicer
from .proto import bot_pb2_grpc
from src.config.settings import Settings

settings = Settings()

logging.basicConfig(level=settings.log_level, format='{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}')

logger = logging.getLogger(__name__)

# Create FastAPI app for health checks
app = FastAPI()

@app.get("/health/live", status_code=status.HTTP_200_OK)
async def liveness_check() -> Dict:
    """
    Liveness probe - checks if the service is running
    Returns 200 if the service is alive
    """
    return {
        "status": "alive",
        "service": "bot-service",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health/ready", status_code=status.HTTP_200_OK)
async def readiness_check() -> Dict:
    """
    Readiness probe - checks if the service can handle requests
    """
    return {
        "status": "ready",
        "service": "bot-service",
        "timestamp": datetime.utcnow().isoformat()
    }

def run_grpc_server(loop):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    bot_servicer = BotServiceServicer()
    bot_servicer.loop = loop
    bot_pb2_grpc.add_BotServiceServicer_to_server(bot_servicer, server)
    server.add_insecure_port(f'[::]:{settings.grpc_port}')
    server.start()
    logger.info(f"Bot service started on port {settings.grpc_port}")
    server.wait_for_termination()

def run_fastapi_server():
    uvicorn.run(app, host="0.0.0.0", port=8080)

def serve():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Start gRPC server in a thread
    server_thread = threading.Thread(target=run_grpc_server, args=(loop,))
    server_thread.start()
    
    # Start FastAPI server in a thread
    health_thread = threading.Thread(target=run_fastapi_server)
    health_thread.start()
    
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()

if __name__ == '__main__':
    serve()