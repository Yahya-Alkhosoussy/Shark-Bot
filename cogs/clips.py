import discord
from discord import app_commands
from discord.ext import commands

from SQL.clipManagement.clips import add_user, get_nick, get_username
from utils.pullingFromTwitch import get_clips


class Clips(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="add_channel_for_clips", description="Add your channel to get ur clips sent somewhere after ur stream"
    )
    @app_commands.describe()
    async def add_channel_to_clips(self, interaction: discord.Interaction, twitch_username: str, to_dms: str, channel_id: int):
        await interaction.response.send_message("Adding your twitch username to our database...")
        username = twitch_username
        user = interaction.user
        if to_dms.lower() == "yes":
            await add_user(discord_id=user.id, user=user.name, username=username, dms=True)
        else:
            await add_user(discord_id=user.id, user=user.name, username=username, dms=False, channel_id=channel_id)

    @app_commands.command(name="clips", description="Get twitch clips manually")
    async def clips(self, interaction: discord.Interaction, days_ago: int, hours_ago: int, minutes_ago: int):
        await interaction.response.send_message("Getting your clips")
        username = get_username(interaction.user.id)
        nick = get_nick(interaction.user.id)

        clips = await get_clips(username, days_ago, hours_ago, minutes_ago, user=nick)

        print("Clips gotten")

        channel = interaction.channel

        messages = []
        to_send = "Here are the clips you requested: \n"

        for clip in clips:
            if len(to_send) + len(clip) + 1 > 2000:
                messages.append(to_send)
                to_send = clip + "\n"
            else:
                to_send += clip + "\n"
        if len(messages) == 0:
            messages.append(to_send)
        for message in messages:
            if isinstance(channel, discord.TextChannel):
                await channel.send(message)
