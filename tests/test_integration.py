import pytest
import grpc
import asyncio
from concurrent import futures

from proto import bot_pb2, bot_pb2_grpc
from bot.service import BotServiceServicer

@pytest.fixture(scope="module")
def grpc_server():
    """Provide a running gRPC server for integration tests."""
    # Create and start server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    bot_pb2_grpc.add_BotServiceServicer_to_server(
        BotServiceServicer(), server
    )
    port = server.add_insecure_port('[::]:50051')
    server.start()
    
    yield f'localhost:{port}'
    
    # Cleanup
    server.stop(grace=None)
    server.wait_for_termination()

@pytest.fixture(scope="module")
def grpc_channel(grpc_server):
    """Provide a gRPC channel connected to our test server."""
    return grpc.insecure_channel(grpc_server)

@pytest.fixture
def stub(grpc_channel):
    """Provide a service stub for making calls."""
    return bot_pb2_grpc.BotServiceStub(grpc_channel)

def test_full_bot_lifecycle(stub):
    """Test the complete lifecycle of a bot through the gRPC interface."""
    # Create a bot
    bot = bot_pb2.Bot(
        game_id="integration_test_game",
        difficulty="hard",
        strategy="aggressive"
    )
    create_response = stub.CreateBot(
        bot_pb2.CreateBotRequest(bot_id="test_bot", bot=bot)
    )
    assert create_response.status == "created"
    
    # Get bot information
    get_response = stub.GetBot(
        bot_pb2.GetBotRequest(bot_id="test_bot")
    )
    assert get_response.game_id == "integration_test_game"
    
    # List bots
    list_response = stub.ListBots(bot_pb2.Empty())
    assert "test_bot" in list_response.bots
    
    # Delete bot
    stub.DeleteBot(bot_pb2.DeleteBotRequest(bot_id="test_bot"))
    
    # Verify deletion
    with pytest.raises(grpc.RpcError) as exc_info:
        stub.GetBot(bot_pb2.GetBotRequest(bot_id="test_bot"))
    assert exc_info.value.code() == grpc.StatusCode.NOT_FOUND

def test_concurrent_bot_operations(stub):
    """Test handling multiple concurrent bot operations."""
    # Create multiple bots concurrently
    bot_ids = [f"concurrent_bot_{i}" for i in range(5)]
    
    for bot_id in bot_ids:
        bot = bot_pb2.Bot(
            game_id="concurrent_test_game",
            difficulty="medium"
        )
        stub.CreateBot(bot_pb2.CreateBotRequest(bot_id=bot_id, bot=bot))
    
    # List all bots
    list_response = stub.ListBots(bot_pb2.Empty())
    assert all(bot_id in list_response.bots for bot_id in bot_ids)
    
    # Delete all bots concurrently
    for bot_id in bot_ids:
        stub.DeleteBot(bot_pb2.DeleteBotRequest(bot_id=bot_id))
    
    # Verify all bots are deleted
    final_list = stub.ListBots(bot_pb2.Empty())
    assert all(bot_id not in final_list.bots for bot_id in bot_ids)