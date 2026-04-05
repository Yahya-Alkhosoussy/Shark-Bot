import pytest
from unittest.mock import MagicMock, patch
from loops.birthdayloop.birthdayLoop import BirthdayLoop
from loops.clipping.clips import ClipLoop
from loops.levellingloop.levellingLoop import levelingLoop
from loops.sharkGameLoop.sharkGameLoop import SharkLoops
from loops.twitchliveloop.TwitchLiveLoop import TwitchLiveLoop
from socialMedia.tiktok import TikTokLoop
from freezegun import freeze_time


@pytest.fixture
def birthday_cog(mock_client, mock_config):
    instance = BirthdayLoop(mock_client, mock_config)
    return instance

@pytest.mark.asyncio
async def test_tick_sends_birthday_message_for_one_user(birthday_cog, mock_channel, mock_birthday_handler, mock_member):
    
    guild_id = 123456
    # control today's date
    mock_birthday_handler.get_birthdays = MagicMock(return_value=([mock_member.id], ["04-04"]))

    with patch("loops.birthdayloop.birthdayLoop.b", mock_birthday_handler), patch("discord.ext.tasks.Loop.start"):
        birthday_cog.start_for(guild_id)
        
        loop = birthday_cog._loops[guild_id]
        await loop.coro()

    mock_birthday_handler.get_birthdays.assert_called_once()

@freeze_time("2026-01-01 12:00:00-06:00") # To freeze time on the first of jan 2026 for chicago timezone
@pytest.mark.asyncio
async def test_tick_sends_birthday_message_first_of_month(birthday_cog, mock_channel, mock_config, mock_birthday_handler, mock_member):
    guild_id = 123456
    mock_config.birthday_message["January"] = False

    mock_birthday_handler.get_birthdays = MagicMock(return_value=([], []))

    with patch("loops.birthdayloop.birthdayLoop.b", mock_birthday_handler),\
         patch("discord.ext.tasks.Loop.start"):
        birthday_cog.start_for(guild_id)


        loop = birthday_cog._loops[guild_id]
        await loop.coro()

    mock_channel.send.assert_called_once_with("Happy Birthday to <@&1335413563627409429>")
    mock_config.mark_reminder_as_done.assert_called_once_with("January")

@pytest.fixture
def clip_cog(mock_config, mock_bot):
    return ClipLoop(mock_bot, mock_config)

@pytest.mark.asyncio
async def test_clip_loop_sends(clip_cog, mock_clip_handler, mock_channel):
    guild_id = 123456

    with patch("discord.ext.tasks.Loop.start"):
        clip_cog.start_for(guild_id)

        loop = clip_cog._loops[guild_id]
        await loop.coro()
    mock_channel.send.assert_called()

@pytest.fixture
def leveling_cog(mock_bot):
    return levelingLoop(mock_bot)

@pytest.mark.asyncio
async def test_leveling_loop_message_handle(leveling_cog, mock_channel, mock_message, mock_level_sql):

    mock_message.content = "This is a test message"

    with patch("loops.levellingloop.levellingLoop.ls", mock_level_sql):
        await leveling_cog.message_handle(mock_message)
    
    mock_channel.send.assert_called_once()

@pytest.mark.asyncio
async def test_leveling_loop_add_and_remove_role(leveling_cog, mock_member, mock_level_config, mock_level_sql):
    with patch("loops.levellingloop.levellingLoop.ls", mock_level_sql):
        await leveling_cog.add_role(mock_member)
    
    mock_member.add_roles.assert_called_once()
    mock_member.remove_roles.assert_called_once()

@pytest.fixture
def shark_cog(mock_client, mock_config):
    return SharkLoops(mock_client, mock_config)

@pytest.mark.parametrize("random_number_2, expected_message", [
        (1, "A legendary Reef Shark has escaped, no one caught it. 😞"),
        (4, "A shiny Reef Shark has escaped, no one caught it. 😞"),
        (10,"A normal Reef Shark has escaped, no one caught it. 😞"),
    ])
@pytest.mark.asyncio
async def test_shark_loop_no_winner(shark_cog, mock_channel, mock_fishing_config, mock_shark_sql, mock_remove_net_use, random_number_2, expected_message):
    guild_id = 123456
    partial_path = "loops.sharkGameLoop.sharkGameLoop"
    with patch("discord.ext.tasks.Loop.start"), \
         patch(partial_path + ".sg", mock_shark_sql),\
         patch(partial_path + ".FishingConfig", mock_fishing_config), \
         patch(partial_path + ".get_warning", mock_remove_net_use), \
         patch(partial_path + ".time.monotonic") as mock_time, \
         patch(partial_path + ".random.randint", side_effect=[5, 0, random_number_2, 0]):
        mock_time.return_value = 0.0
        shark_cog.check_interval = 5
        shark_cog.start_for(guild_id)

        loop = shark_cog._loops[guild_id]
        await loop.coro()
    mock_channel.send.assert_any_call("A shark just appeared 🦈! Quick, type `?catch` within 2 minutes to catch it 🎣")
    mock_channel.send.assert_any_call(expected_message)


@pytest.fixture
def shark_cog_winner(mock_client_winner, mock_config):
    return SharkLoops(mock_client_winner, mock_config)


@pytest.mark.parametrize("random_number_2, expected_message", [
    (1, "Congratulations to BadUser who caught a legendary Reef Shark 👏. You have been granted 20"),
    (4, "Congratulations to BadUser who caught a shiny Reef Shark 👏. You have been granted 20"),
    (10,"Congratulations to BadUser who caught a normal Reef Shark 👏. You have been granted 20"),
])
@pytest.mark.asyncio
async def test_shark_loop_one_winner_no_net(shark_cog_winner, mock_channel, mock_fishing_config, mock_shark_sql, mock_remove_net_use, random_number_2, expected_message):
    guild_id = 123456
    partial_path = "loops.sharkGameLoop.sharkGameLoop"
    with patch("discord.ext.tasks.Loop.start"), \
         patch(partial_path + ".sg", mock_shark_sql),\
         patch(partial_path + ".FishingConfig", mock_fishing_config), \
         patch(partial_path + ".get_warning", mock_remove_net_use), \
         patch(partial_path + ".time.monotonic") as mock_time, \
         patch(partial_path + ".random.randint", side_effect=[5, 0, random_number_2, 100]):
        mock_time.side_effect = [
            220,
            219.4,
            219.6
        ]
        shark_cog_winner.check_interval = 5
        shark_cog_winner.start_for(guild_id)

        loop = shark_cog_winner._loops[guild_id]
        await loop.coro()
    mock_channel.send.assert_any_call("A shark just appeared 🦈! Quick, type `?catch` within 2 minutes to catch it 🎣")
    mock_channel.send.assert_any_call(expected_message)

@pytest.fixture
def twitch_live_cog(mock_client, mock_config):
    return TwitchLiveLoop(mock_client, mock_config)

@pytest.mark.asyncio
async def test_twitch_live_loop(twitch_live_cog, mock_channel, mock_twitch_sql, mock_twitch_api):
    guild_id = 123456
    with patch("discord.ext.tasks.Loop.start"):
        twitch_live_cog.start_for(guild_id)

        loop = twitch_live_cog._loops[guild_id]
        await loop.coro()
    mock_channel.send.assert_called_once()

@pytest.fixture
def tiktok_cog(mock_client, mock_config):
    return TikTokLoop(mock_client, mock_config)

@pytest.mark.asyncio
async def test_tiktok_loop(tiktok_cog, mock_channel, mock_tiktok_sql, mock_tiktok_api):
    guild_id = 123456
    with patch("discord.ext.tasks.Loop.start"):
        tiktok_cog.start_for(guild_id)

        loop = tiktok_cog._loops[guild_id]
        await loop.coro()
    mock_channel.send.assert_called_once()