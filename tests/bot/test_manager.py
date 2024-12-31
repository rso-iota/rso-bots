import pytest
import asyncio
from proto.bot_pb2 import Bot
from bot.service import BotManager

@pytest.fixture
def bot_manager():
    """Provide a fresh BotManager instance for each test."""
    return BotManager()

@pytest.fixture
def sample_bot():
    """Provide a sample bot configuration."""
    return Bot(
        game_id="test_game",
        difficulty="medium",
        strategy="defensive"
    )

@pytest.mark.asyncio
async def test_add_bot(bot_manager, sample_bot):
    """Test adding a new bot."""
    bot_id = "test_bot_1"
    await bot_manager.add_bot(bot_id, sample_bot)
    
    assert bot_id in bot_manager._bots
    assert bot_id in bot_manager._tasks
    assert bot_manager._bots[bot_id].game_id == "test_game"
    assert not bot_manager._tasks[bot_id].done()

@pytest.mark.asyncio
async def test_add_duplicate_bot(bot_manager, sample_bot):
    """Test adding a bot with an ID that already exists."""
    bot_id = "test_bot_1"
    await bot_manager.add_bot(bot_id, sample_bot)
    
    with pytest.raises(ValueError, match="already exists"):
        await bot_manager.add_bot(bot_id, sample_bot)

@pytest.mark.asyncio
async def test_remove_bot(bot_manager, sample_bot):
    """Test removing an existing bot."""
    bot_id = "test_bot_1"
    await bot_manager.add_bot(bot_id, sample_bot)
    await bot_manager.remove_bot(bot_id)
    
    assert bot_id not in bot_manager._bots
    assert bot_id not in bot_manager._tasks

@pytest.mark.asyncio
async def test_remove_nonexistent_bot(bot_manager):
    """Test removing a bot that doesn't exist."""
    with pytest.raises(ValueError, match="does not exist"):
        await bot_manager.remove_bot("nonexistent_bot")

@pytest.mark.asyncio
async def test_bot_task_cleanup_on_removal(bot_manager, sample_bot):
    """Test that bot tasks are properly cleaned up when removed."""
    bot_id = "test_bot_1"
    await bot_manager.add_bot(bot_id, sample_bot)
    
    # Get the task before removal
    task = bot_manager._tasks[bot_id]
    
    await bot_manager.remove_bot(bot_id)
    
    # Verify task is cancelled and cleanup is complete
    assert task.cancelled()
    assert bot_id not in bot_manager._tasks
    
@pytest.mark.asyncio
async def test_multiple_bots(bot_manager, sample_bot):
    """Test managing multiple bots simultaneously."""
    bot_ids = ["bot1", "bot2", "bot3"]
    
    # Add multiple bots
    for bot_id in bot_ids:
        await bot_manager.add_bot(bot_id, sample_bot)
    
    # Verify all bots are running
    assert len(bot_manager._bots) == len(bot_ids)
    assert all(not bot_manager._tasks[bot_id].done() for bot_id in bot_ids)
    
    # Remove one bot
    await bot_manager.remove_bot(bot_ids[0])
    assert len(bot_manager._bots) == len(bot_ids) - 1
    assert bot_ids[0] not in bot_manager._tasks