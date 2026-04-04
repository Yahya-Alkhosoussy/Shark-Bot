import pytest
from moderation.tools import Moderation
from datetime import timedelta

@pytest.fixture
def cog(mock_bot, mock_config):
    return Moderation(mock_bot, mock_config)

@pytest.mark.asyncio
async def test_ban_sends_confirmation(cog, mock_ctx, mock_member):
    await cog.ban.callback(cog, ctx=mock_ctx, member=mock_member, reason="Spamming")

    mock_member.ban.assert_called_once_with(reason="Spamming")
    mock_ctx.send.assert_called_once_with("BadUser has been banned.")

@pytest.mark.asyncio
async def test_ban_uses_default_reason(cog, mock_ctx, mock_member):
    await cog.ban.callback(cog, ctx=mock_ctx, member=mock_member)

    mock_member.ban.assert_called_once_with(reason="No Reason Provided")

@pytest.mark.asyncio
async def test_kick_sends_confirmation(cog, mock_ctx, mock_member):
    await cog.kick.callback(cog, ctx=mock_ctx, member=mock_member, reason="Spamming")

    mock_member.kick.assert_called_once_with(reason="Spamming")
    mock_ctx.send.assert_called_once_with("BadUser has been kicked.")

@pytest.mark.asyncio
async def test_kick_uses_default_reason(cog, mock_ctx, mock_member):
    await cog.kick.callback(cog, ctx=mock_ctx, member=mock_member)
    
    mock_member.kick.assert_called_once_with(reason="No Reason Provided")

@pytest.mark.asyncio
async def test_timeout_sends_confirmation(cog, mock_ctx, mock_member):
    duration = 120
    await cog.timeout.callback(cog, ctx=mock_ctx, member=mock_member, reason="Spamming", duration=duration)

    mock_member.timeout.assert_called_once_with(timedelta(seconds=duration), reason="Spamming")
    mock_ctx.send.assert_called_once_with("BadUser has been timedout.")

@pytest.mark.asyncio
async def test_timeout_uses_default_reason(cog, mock_ctx, mock_member):
    duration = 120

    await cog.timeout.callback(cog, ctx=mock_ctx, member=mock_member, duration=duration)
    
    mock_member.timeout.assert_called_once_with(timedelta(seconds=duration), reason="No Reason Provided")