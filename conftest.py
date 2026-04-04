import pytest
from unittest.mock import AsyncMock, MagicMock
import discord

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
    member.mention = "<@987654321>"
    member.id = 987654321
    return member

@pytest.fixture
def mock_config():
    config = MagicMock()
    config.send_discord_mod_log = AsyncMock()
    config.check_for_mod_role = MagicMock(return_value=True)
    config.birthday_message = {
        "January": False,
        "February": False,
        "March": False,
        "April": False,
        "May": False,
        "June": False,
        "July": False,
        "August": False,
        "September": False,
        "October": False,
        "November": False,
        "December": False,
    }
    config.guilds = {123456: "TestGuild"}
    config.get_channel_id = MagicMock(return_value=11112223333444)
    config.mark_reminder_as_done = MagicMock(return_value=True)
    return config

@pytest.fixture
def mock_channel():
    channel = MagicMock(spec=discord.TextChannel) # important because of isinstance
    channel.send = AsyncMock()
    return channel

@pytest.fixture
def mock_client(mock_member, mock_channel):
    client = MagicMock()
    client.get_channel = MagicMock(return_value=mock_channel)
    client.fetch_user = AsyncMock(return_value=mock_member)
    return client

@pytest.fixture
def mock_birthday_handler():
    b = MagicMock()
    b.get_birthdays = MagicMock(return_value=([], [])) # User_ids, birthdays
    b.has_custom_gif = MagicMock(return_value=None)
    b.get_number_of_gifs = MagicMock(return_value=3)
    b.get_gif = MagicMock(return_value="https://example.com/gif.gif")
    b.get_number_of_messages = MagicMock(return_value=3)
    b.get_birthday_message = MagicMock(return_value="Happy Birthday @user!")
    b.get_custom_gifs = MagicMock(return_value="https://example.com/custom.gif")
    return b

@pytest.fixture
def mock_cog(mock_client, mock_config):
    cog = MagicMock()
    cog.client = mock_client
    cog.config = mock_config
    return cog