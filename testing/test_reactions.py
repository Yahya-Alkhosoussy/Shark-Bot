import pytest
from handlers.reactions import reaction_handler

@pytest.fixture
def reaction_cog(mock_config, mock_roles_per_guild, mock_client):
    return reaction_handler(mock_config, mock_roles_per_guild, mock_client)

@pytest.mark.asyncio
async def test_reaction_handler(reaction_cog, mock_channel, mock_guild, mock_roles_per_guild):
    await reaction_cog.ensure_react_roles_message_internal(mock_guild, mock_roles_per_guild)

    mock_channel.send.assert_called()