import pytest
import grpc
from unittest.mock import MagicMock
from concurrent import futures
from proto import bot_pb2, bot_pb2_grpc
from bot.service import BotServiceServicer

class MockContext:
    """Mock gRPC context for testing."""
    def __init__(self):
        self.code = grpc.StatusCode.OK
        self.details = ""
    
    def set_code(self, code):
        self.code = code
    
    def set_details(self, details):
        self.details = details

@pytest.fixture
def service():
    """Provide a fresh service instance for each test."""
    return BotServiceServicer()

@pytest.fixture
def context():
    """Provide a mock gRPC context."""
    return MockContext()

@pytest.fixture
def sample_bot_request():
    """Provide a sample bot creation request."""
    bot = bot_pb2.Bot(
        game_id="test_game",
        difficulty="medium",
        strategy="defensive"
    )
    return bot_pb2.CreateBotRequest(bot_id="test_bot", bot=bot)

def test_create_bot(service, context, sample_bot_request):
    """Test creating a new bot through the gRPC interface."""
    response = service.CreateBot(sample_bot_request, context)
    
    assert response.bot_id == sample_bot_request.bot_id
    assert response.status == "created"
    assert context.code == grpc.StatusCode.OK

def test_create_duplicate_bot(service, context, sample_bot_request):
    """Test attempting to create a bot with a duplicate ID."""
    # Create first bot
    service.CreateBot(sample_bot_request, context)
    
    # Attempt to create duplicate
    response = service.CreateBot(sample_bot_request, context)
    
    assert context.code == grpc.StatusCode.ALREADY_EXISTS
    assert "already exists" in context.details

def test_delete_bot(service, context, sample_bot_request):
    """Test deleting an existing bot."""
    # First create a bot
    service.CreateBot(sample_bot_request, context)
    
    # Then delete it
    delete_request = bot_pb2.DeleteBotRequest(bot_id=sample_bot_request.bot_id)
    service.DeleteBot(delete_request, context)
    
    assert context.code == grpc.StatusCode.OK

def test_delete_nonexistent_bot(service, context):
    """Test attempting to delete a nonexistent bot."""
    delete_request = bot_pb2.DeleteBotRequest(bot_id="nonexistent")
    service.DeleteBot(delete_request, context)
    
    assert context.code == grpc.StatusCode.NOT_FOUND

def test_get_bot(service, context, sample_bot_request):
    """Test retrieving bot information."""
    # First create a bot
    service.CreateBot(sample_bot_request, context)
    
    # Then get its information
    get_request = bot_pb2.GetBotRequest(bot_id=sample_bot_request.bot_id)
    bot = service.GetBot(get_request, context)
    
    assert bot.game_id == sample_bot_request.bot.game_id
    assert bot.difficulty == sample_bot_request.bot.difficulty
    assert bot.strategy == sample_bot_request.bot.strategy

def test_get_nonexistent_bot(service, context):
    """Test attempting to get information about a nonexistent bot."""
    get_request = bot_pb2.GetBotRequest(bot_id="nonexistent")
    service.GetBot(get_request, context)
    
    assert context.code == grpc.StatusCode.NOT_FOUND

def test_list_bots(service, context, sample_bot_request):
    """Test listing all active bots."""
    # Create a few bots
    bot_ids = ["bot1", "bot2", "bot3"]
    for bot_id in bot_ids:
        request = bot_pb2.CreateBotRequest(
            bot_id=bot_id,
            bot=sample_bot_request.bot
        )
        service.CreateBot(request, context)
    
    # List all bots
    response = service.ListBots(bot_pb2.Empty(), context)
    
    assert len(response.bots) == len(bot_ids)
    assert all(bot_id in response.bots for bot_id in bot_ids)