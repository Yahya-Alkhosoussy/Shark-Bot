import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import discord
from utils.leveling import LevelRole, LevelRoleSet, LevelingConfig
from pathlib import Path
import asyncio

CONFIG_PATH = Path(r"loops\levellingloop\levelingConfig.yaml")
config = LevelingConfig(CONFIG_PATH)

roles: LevelRoleSet = config.level_roles['shark squad']

@pytest.fixture
def mock_bot(mock_channel):
    bot = MagicMock()
    bot.user = MagicMock()
    bot.user.id = 123456789
    bot.get_channel = MagicMock(return_value=mock_channel)
    return bot

@pytest.fixture
def mock_ctx(mock_guild):
    ctx = MagicMock()
    ctx.send = AsyncMock() # since ctx.send is an Async function
    ctx.author = MagicMock()
    ctx.author.id = 987654321
    ctx.author.name = "TestUser"
    ctx.guild = mock_guild
    ctx.guild.id = mock_guild.id
    return ctx

@pytest.fixture
def mock_member(mock_guild, mock_role):
    member = MagicMock(spec=discord.Member)
    member.ban = AsyncMock()
    member.kick = AsyncMock()
    member.timeout = AsyncMock()
    member.name = "BadUser"
    member.nick = None
    member.mention = "<@987654321>"
    member.id = 987654321
    member.guild = mock_guild
    member.guild.id = mock_guild.id
    member.add_roles.return_value = True
    member.remove_roles.return_value = True
    member.roles = list(mock_role)
    return member

@pytest.fixture
def mock_role():
    role = MagicMock()
    role.id = roles["4"]
    return role

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
    config.reload.return_value = None
    config.time_per_loop = 5
    config.window_time = 0.4
    return config

@pytest.fixture
def mock_channel():
    channel = MagicMock(spec=discord.TextChannel) # important because of isinstance
    channel.send = AsyncMock()
    return channel

@pytest.fixture
def mock_client(mock_member, mock_channel, mock_message):
    client = MagicMock()
    client.get_channel = MagicMock(return_value=mock_channel)
    client.fetch_user = AsyncMock(return_value=mock_member)
    
    client.wait_for = AsyncMock(side_effect=asyncio.TimeoutError)
    return client

@pytest.fixture
def mock_client_winner(mock_member, mock_channel, mock_message):
    client = MagicMock()
    client.get_channel = MagicMock(return_value=mock_channel)
    client.fetch_user = AsyncMock(return_value=mock_member)
    client.wait_for = AsyncMock(side_effect=[mock_message, asyncio.TimeoutError])
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

@pytest.fixture
def mock_level_config():
    config = MagicMock()
    config.level_roles = {
        "shark squad": LevelRoleSet([
            LevelRole(level=1, id=roles["1"]),
            LevelRole(level=2, id=1462838512993697975),
            LevelRole(level=3, id=1462838533940056236),
            LevelRole(level=4, id=1462838552634200229),
            LevelRole(level=5, id=1462832730176880771)
        ])}
    config.reload.return_value = None
    config.__getitem__ = MagicMock(side_effect={
        "boost": False,
        "boost amount": 2,
    }.__getitem__)
    return config

@pytest.fixture
def mock_level_sql():
    ls = MagicMock()
    ls.add_user.return_value = True
    ls.get_info.return_value = (4, 0, 0, 2)
    ls.add_to_level.return_value = None
    ls.check_level.return_value = True
    return ls

@pytest.fixture
def mock_message(mock_member, mock_channel):
    message = MagicMock(spec=discord.Message)
    message.content = "?catch"
    message.author = mock_member
    message.channel = mock_channel
    message.author.bot = False
    return message

@pytest.fixture
def mock_guild():
    guild = MagicMock()
    guild.id = 1234567
    guild.get_role.return_value = True
    return guild

@pytest.fixture
def mock_fishing_config():
    config = MagicMock()
    config.boost = False
    config.boost_amount = 2
    return config

@pytest.fixture
def mock_shark_sql():
    sg = MagicMock()
    sg.get_names_of_sharks.return_value = ["Reef Shark"]
    sg.get_shark_names.return_value = ["Reef Shark"]
    sg.is_net_available.return_value = False
    sg.fishing_odds_shark.return_value = 100
    sg.create_dex.return_value = None
    sg.reward_coins.return_value = 20
    sg.remove_net_use.return_value = None
    sg.remove_net.return_value = None
    return sg

@pytest.fixture
def mock_remove_net_use():
    remove_net_use = MagicMock()
    remove_net_use.return_value = (None, -1)
    return remove_net_use