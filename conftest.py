import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_bot():
    bot = MagicMock()
    bot.user = MagicMock()
    bot.user.id = 123456789
    return bot

@pytest.fixture
def mock_ctx():
    ctx = MagicMock()
    ctx.send = AsyncMock() # since ctx.send is an Async function
    ctx.author = MagicMock()
    ctx.author.id = 987654321
    ctx.author.name = "TestUser"
    ctx.guild = MagicMock()
    ctx.guild.id = 1234567
    return ctx

@pytest.fixture
def mock_member():
    member = MagicMock()
    member.ban = AsyncMock()
    member.kick = AsyncMock()
    member.timeout = AsyncMock()
    member.name = "BadUser"
    member.nick = None
    return member

@pytest.fixture
def mock_config():
    config = MagicMock()
    config.send_discord_mod_log = AsyncMock()
    config.check_for_mod_role = MagicMock(return_value=True)
    return config
