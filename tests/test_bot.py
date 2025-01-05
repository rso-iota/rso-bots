import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from src.bot.strategy import BotStrategy
from src.bot.game_client import GameClient
from src.bot.bot_manager import BotManager, BotInstance
from src.config.settings import Settings

settings = Settings()

@pytest.fixture
def game_state():
    return {
        "players": [
            {
                "name": "TestBot",
                "alive": True,
                "circle": {
                    "x": 100,
                    "y": 100,
                    "radius": 10
                }
            }
        ],
        "food": [
            {
                "index": 0,
                "circle": {
                    "x": 200,
                    "y": 200,
                    "radius": 5
                }
            }
        ]
    }

@pytest.fixture
def strategy():
    return BotStrategy()

def test_strategy_calculates_move(strategy, game_state):
    dx, dy = strategy.calculate_move(game_state, "TestBot")
    # Should move towards food at (200, 200)
    assert dx > 0  # Should move right
    assert dy > 0  # Should move down
    
    # Vector should be normalized
    length = (dx * dx + dy * dy) ** 0.5
    assert abs(length - 1.0) < 1e-6

@pytest.mark.asyncio
async def test_bot_manager_creates_bot():
    manager = BotManager(settings)
    
    # Mock the client and strategy
    with patch("src.bot.bot_manager.GameClient") as mock_client, \
         patch("src.bot.bot_manager.BotStrategy") as mock_strategy:
        
        # Configure mock with AsyncMock for async methods
        mock_client_instance = MagicMock()
        mock_client_instance.connect = AsyncMock()  # Make connect an async mock
        mock_client_instance.handle_messages = AsyncMock()  # Also mock handle_messages
        mock_client.return_value = mock_client_instance
        
        # Create a bot
        bot_id = await manager.create_bot("TestBot", "game1")
        
        assert bot_id in manager.bots
        assert manager.bots[bot_id].name == "TestBot"
        

@pytest.mark.asyncio
async def test_bot_manager_removes_bot():
    manager = BotManager(settings)
    
    # Mock the client and strategy
    with patch("src.bot.bot_manager.GameClient") as mock_client:
        # Configure mock with AsyncMock
        mock_client_instance = MagicMock()
        mock_client_instance.connect = AsyncMock()
        mock_client_instance.handle_messages = AsyncMock()
        mock_client_instance.websocket = MagicMock()
        mock_client_instance.websocket.close = AsyncMock()
        mock_client.return_value = mock_client_instance
        
        # Create and then remove a bot
        bot_id = await manager.create_bot("TestBot", "game1")
        assert bot_id in manager.bots
        
        success = await manager.remove_bot(bot_id)
        assert success
        assert bot_id not in manager.bots

def test_strategy_finds_nearest_food(strategy):
    position = {"x": 0, "y": 0}
    food_list = [
        {"circle": {"x": 1, "y": 2}},
        {"circle": {"x": 2, "y": 2}},
        {"circle": {"x": -1, "y": -1}}
    ]
    
    nearest = strategy.find_nearest_food(position, food_list)
    assert nearest["circle"]["x"] == -1
    assert nearest["circle"]["y"] == -1
