import asyncio
from datetime import timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from utils.core import RoleMessage, RoleMessageSet
from utils.leveling import LevelingConfig, LevelRole, LevelRoleSet
from utils.socials.youtubeCore import core

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
def mock_member(mock_role):
    member = MagicMock(spec=discord.Member)
    member.ban = AsyncMock()
    member.kick = AsyncMock()
    member.timeout = AsyncMock()
    member.name = "BadUser"
    member.nick = None
    member.mention = "<@987654321>"
    member.id = 987654321
    member.guild = MagicMock(spec=discord.Guild)  # inline, not the fixture
    member.guild.id = 123456
    member.add_roles.return_value = True
    member.remove_roles.return_value = True
    member.roles = list(mock_role)
    return member

@pytest.fixture
def mock_role():
    role = MagicMock()
    role.id = roles["4"]
    role.mention = "mentionable string"
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
    config.guild_role_messages = {None: RoleMessageSet([RoleMessage("Role Set", 0)])}
    config.is_rr_message_id_in_config = MagicMock(return_value=True)
    config.is_guild_in_config = MagicMock(return_value=True)
    return config

@pytest.fixture
def mock_channel(mock_message):
    channel = MagicMock(spec=discord.TextChannel) # important because of isinstance
    channel.send = AsyncMock(return_value=mock_message)
    channel.fetch_message = AsyncMock(spec=discord.Message)
    return channel

@pytest.fixture
def mock_client(mock_member, mock_channel, mock_guild):
    client = MagicMock()
    client.get_channel = MagicMock(return_value=mock_channel)
    client.fetch_user = AsyncMock(return_value=mock_member)
    client.get_guild = MagicMock(return_value=mock_guild)
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
def mock_message(mock_member):
    message = MagicMock(spec=discord.Message)
    message.content = "?catch"
    message.author = mock_member
    message.channel = MagicMock(spec=discord.TextChannel)
    message.author.bot = False
    message.id = 112223333444
    return message

@pytest.fixture
def mock_guild(mock_channel, mock_role):
    guild = MagicMock()
    guild.id = 123456
    guild.name = "Test Guild"
    guild.get_role.return_value = mock_role
    guild.get_channel.return_value = mock_channel
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

@pytest.fixture
def mock_twitch_sql():
    partial_path = "loops.twitchliveloop.TwitchLiveLoop"
    with patch(partial_path + ".get_custom_message") as mock_get_custom_message, \
         patch(partial_path + ".get_live_status") as mock_get_live_status, \
         patch(partial_path + ".get_users") as mock_get_users, \
         patch(partial_path + ".update_live_status") as mock_update_live_status:

        mock_get_custom_message.return_value = "BadUser is live!"
        mock_get_live_status.return_value = False
        mock_get_users.return_value = ["BadUser"]
        mock_update_live_status.return_value = None
        yield {
            "get_custom_message": mock_get_custom_message,
            "get_live_status": mock_get_live_status,
            "get_users": mock_get_users,
            "update_live_status": mock_update_live_status,
        }

@pytest.fixture
def mock_twitch_api():
    partial_path = "loops.twitchliveloop.TwitchLiveLoop"
    with patch(partial_path + ".get_profile_picture") as mock_get_profile_picture, \
         patch(partial_path + ".get_stream_details") as mock_get_stream_details, \
         patch(partial_path + ".is_live") as mock_is_live:

        mock_get_profile_picture.return_value = "https://link-to.profile-picture.com"
        mock_get_stream_details.return_value = ("Playing some game", "Some Game", "https://link-to.thumbnail.com")
        mock_is_live.return_value = True
        yield {
            "get_profile_picture": mock_get_profile_picture,
            "get_stream_details": mock_get_stream_details,
            "is_live": mock_is_live
        }

@pytest.fixture
def mock_tiktok_sql(mock_role):
    partial_path = "socialMedia.tiktok"
    with patch(partial_path + ".add_link") as mock_add_link, \
         patch(partial_path + ".check_if_link_exists") as mock_check_if_link_exists, \
         patch(partial_path + ".get_role_id") as mock_get_role_id:

        mock_add_link.return_value = None
        mock_check_if_link_exists.return_value = False
        mock_get_role_id.return_value = mock_role.id
        yield {
            "add_link": mock_add_link,
            "check_if_link_exists": mock_check_if_link_exists,
            "get_role_id": mock_get_role_id
        }

@pytest.fixture
def mock_tiktok_api():
    with patch("socialMedia.tiktok.get_latest_videos") as mock_get_latest_videos:
        mock_get_latest_videos.return_value = (["https://link-to.video.com"], [123456], ["https://link-to.thumbnail.com"], ["https://link-to.profile-picture.com"])
        yield {"get_latest_videos": mock_get_latest_videos}

@pytest.fixture
def mock_youtube_sql(mock_role):
    partial_path = "socialMedia.youtube"
    with patch(partial_path + ".get_role_id") as mock_get_role_id, \
         patch(partial_path + ".add_video") as mock_add_video, \
         patch(partial_path + ".get_youtube_handles") as mock_get_youtube_handles, \
         patch(partial_path + ".is_video_existing") as mock_is_video_existing:

        mock_get_role_id.return_value = mock_role.id
        mock_add_video.return_value = None
        mock_get_youtube_handles.return_value = set(["BadUser"])
        mock_is_video_existing.return_value = False
        yield {
            "get_role_id": mock_get_role_id,
            "add_video": mock_add_video,
            "get_youtube_handles": mock_get_youtube_handles,
            "is_video_existing": mock_is_video_existing,
        }

@pytest.fixture
def mock_youtube_api():
    partial_path = "socialMedia.youtube"
    with patch(partial_path + ".get_channel_item") as mock_get_channel_item, \
         patch(partial_path + ".get_video_items") as mock_get_video_items:
        mock_get_channel_item.return_value = core.Channel(
            id="verification 1",
            snippet=core.ChannelSnippet(
                title="Video title",
                description="Video Description",
                publishedAt="PublishedAt",
                thumbnails= core.Thumbnails(default=core.ThumbnailInfo(url="https://url-to.thumbnail.com"))
            ))
        mock_get_video_items.return_value = [
            core.PlaylistItem(
                snippet=core.PlaylistItemSnippet(
                    title="Video title",
                    description="Video description",
                    publishedAt="Published at",
                    resourceId=core.ResourceId(kind="Video", videoId="video ID"),
                    thumbnails=core.Thumbnails(default=core.ThumbnailInfo(url="https://url-to.thumbnail.com"))
                )
            )
        ]

        yield {
            "get_channel_item": mock_get_channel_item,
            "get_video_items": mock_get_video_items,
        }

@pytest.fixture
def mock_modActions():
    partial_path = "logModActions.modActions"
    with patch(partial_path + ".add_ban") as mock_add_ban, \
         patch(partial_path + ".add_timeout") as mock_add_timeout, \
         patch(partial_path + ".check_if_timeout_exists") as mock_check_if_timeout_exists, \
         patch(partial_path + ".get_streamers") as mock_get_streamers, \
         patch(partial_path + ".get_timeouts") as mock_get_timeouts, \
         patch(partial_path + ".saved_bans") as mock_saved_bans:

        mock_add_ban.return_value = None
        mock_add_timeout.return_value = None
        mock_check_if_timeout_exists.return_value = False
        mock_get_streamers.return_value = set(["BadUser"])
        mock_get_timeouts.return_value = [(0, "A", "A", "A", "A", 0, "A")]
        mock_saved_bans.return_value = [(0, "A", "A", "A", "A", "A")]

        yield {
            "add_ban": mock_add_ban,
            "add_timeout": mock_add_timeout,
            "check_if_timeout_exists": mock_check_if_timeout_exists,
            "get_streamers": mock_get_streamers,
            "get_timeouts": mock_get_timeouts,
            "saved_bans": mock_saved_bans
        }

@pytest.fixture
def mock_twitch_bans():
    partial_path = "logModActions.modActions"
    with patch(partial_path + ".twitch_bans") as mock_twitch_bans:
        mock_twitch_bans.return_value = (["BannedUser", "TimeoutUser"], ["No Reason", "No Reason"], ["ModUser", "ModUser"], [None, timedelta(seconds=30)], ["2025-07-20", "2025-07-20"])

        yield {
            "twitch_bans": mock_twitch_bans
        }

@pytest.fixture
def mock_roles_per_guild(mock_guild, mock_role):
    map = {}
    map[mock_guild.id] = {}
    map[mock_guild.id]["Role Set"] = {}
    map[mock_guild.id]["Role Set"][discord.PartialEmoji.from_str("🩵")] = mock_role.id
    return map

@pytest.fixture
def mock_roles_sql(mock_roles_per_guild):
    partial_path = "handlers.reactions"
    with patch(partial_path + ".add_role") as mock_add_role, \
         patch(partial_path + ".fill_emoji_map") as mock_fill_emoji_map, \
         patch(partial_path + ".add_message_id_to_table") as mock_add_message_id_to_table, \
         patch(partial_path + ".get_role_messages") as mock_get_role_messages:

        mock_add_role.return_value = None
        mock_fill_emoji_map.return_value = mock_roles_per_guild
        mock_get_role_messages.return_value = (["Role Set"], [0])

        yield {
            "add_role": mock_add_role,
            "fill_emoji_map": mock_fill_emoji_map,
            "get_role_messages": mock_get_role_messages
        }
