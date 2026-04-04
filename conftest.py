import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import discord

@pytest.fixture
def mock_bot(mock_channel):
    bot = MagicMock()
    bot.user = MagicMock()
    bot.user.id = 123456789
    bot.get_channel = MagicMock(return_value=mock_channel)
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

@pytest.fixture
def mock_clip_handler(mock_member):
    partial_path = "loops.clipping.clips"
    with patch(partial_path + ".check_live") as mock_check_live, \
         patch(partial_path + ".get_channel") as mock_get_channel, \
         patch(partial_path + ".get_discord_id") as mock_get_discord_id, \
         patch(partial_path + ".get_nick") as mock_get_nick, \
         patch(partial_path + ".get_users") as mock_get_users, \
         patch(partial_path + ".update_live") as mock_update_live, \
         patch(partial_path + ".internal_handle_stream_end") as mock_internal_handle_stream_end:
        
        mock_check_live.return_value = True
        mock_get_channel.return_value = 123456789
        mock_get_discord_id.return_value = mock_member.id
        mock_get_nick.return_value = mock_member.name
        mock_get_users.return_value = ([mock_member.name], [mock_member.id])
        mock_update_live.return_value = True
        mock_internal_handle_stream_end.return_value = ["Clip 1", "Clip 2", "Clip 3"]
        yield {
            "check_live": mock_check_live,
            "get_channel": mock_get_channel,
            "get_discord_id": mock_get_discord_id,
            "get_nick": mock_get_nick,
            "get_users": mock_get_users,
            "update_live": mock_update_live,
            "internal_handle_stream_end": mock_internal_handle_stream_end,
        }
