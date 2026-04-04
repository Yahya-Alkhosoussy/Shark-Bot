import pytest
from unittest.mock import MagicMock, patch
from loops.birthdayloop.birthdayLoop import BirthdayLoop
from freezegun import freeze_time


@pytest.fixture
def cog(mock_client, mock_config):
    instance = BirthdayLoop(mock_client, mock_config)
    return instance

@pytest.mark.asyncio
async def test_tick_sends_birthday_message_for_one_user(cog, mock_channel, mock_birthday_handler, mock_member):
    
    guild_id = 123456
    # control today's date
    mock_birthday_handler.get_birthdays = MagicMock(return_value=([mock_member.id], ["04-04"]))

    with patch("loops.birthdayloop.birthdayLoop.b", mock_birthday_handler), patch("discord.ext.tasks.Loop.start"):
        cog.start_for(guild_id)
        
        loop = cog._loops[guild_id]
        await loop.coro()

    mock_birthday_handler.get_birthdays.assert_called_once()

@freeze_time("2026-01-01 12:00:00-06:00") # To freeze time on the first of jan 2026 for chicago timezone
@pytest.mark.asyncio
async def test_tick_sends_birthday_message_first_of_month(cog, mock_channel, mock_config, mock_birthday_handler, mock_member):
    guild_id = 123456
    mock_config.birthday_message["January"] = False

    mock_birthday_handler.get_birthdays = MagicMock(return_value=([], []))

    with patch("loops.birthdayloop.birthdayLoop.b", mock_birthday_handler),\
         patch("discord.ext.tasks.Loop.start"):
        cog.start_for(guild_id)


        loop = cog._loops[guild_id]
        await loop.coro()

    mock_channel.send.assert_called_once_with("Happy Birthday to <@&1335413563627409429>")
    mock_config.mark_reminder_as_done.assert_called_once_with("January")
