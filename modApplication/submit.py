import asyncio  # noqa: F401
import io  # noqa: F401
import logging
import sqlite3
from datetime import datetime  # noqa: F401
from pathlib import Path
from zoneinfo import ZoneInfo

import chat_exporter  # noqa: F401
import discord
from pydantic import ValidationError

from utils.ticketing import TicketingConfig

try:
    config = TicketingConfig(Path(r"modApplication\config.yaml"))
except ValidationError as e:
    logging.critical(f"[MOD APPLICATION] Unable to load config {e}")
    raise e
timezone = ZoneInfo("America/Chicago")

conn = sqlite3.connect("databases/mod_applications.db")
cur = conn.cursor()


class submit(discord.ui.View):
    def __init__(self, bot: discord.Client):
        self.bot = bot
        super().__init__(timeout=None)

    @discord.ui.button(label="Submit application", style=discord.ButtonStyle.blurple, custom_id="submit")
    async def submit(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_ids: list[int] = []
        for guild in config.guilds:
            guild_ids.append(guild[1][2])
        if interaction.guild and interaction.guild.id in guild_ids:
            guild_id = interaction.guild.id
        else:
            raise ValueError(
                f"Guild ID {interaction.guild.id if interaction.guild else 'NULL'} not found in GUILD_IDS.values()"
            )

        guild = self.bot.get_guild(guild_id)
        guild_log_channels = config.log_channels[config.guilds[guild_id]]
        mod_app_channel = self.bot.get_channel(guild_log_channels["mod app"])
        if not isinstance(mod_app_channel, discord.TextChannel):
            raise TypeError("Tech support channel is not a Text Channel!")
        channel_id = interaction.channel.id if interaction.channel else None

        # RESPOND IMMEDIATELY
        embed = discord.Embed(description="⏳ submitting application...", color=0xFF0000)
        await interaction.response.send_message(embed=embed)

        cur.execute("SELECT id, discord_id, ticket_created FROM application WHERE ticket_channel=?", (channel_id,))
        app_data = cur.fetchone()
        if app_data is None:
            logging.warning("[TICKETING SYSTEM] app_data is None")
            return
        id, ticket_creator_id, ticket_created = app_data
        ticket_creator = guild.get_member(ticket_creator_id) if guild else None
        ticket_created_unix = self.convert_to_unix_timestamp(ticket_created)
        ticket_closed = datetime.now(timezone).strftime(r"%Y-%m-%d %H:%M:%S")
        ticket_closed_unix = self.convert_to_unix_timestamp(ticket_closed)

        try:
            military_time: bool = True
            transcript = await chat_exporter.export(
                interaction.channel, limit=200, tz_info="America/Chicago", military_time=military_time, bot=self.bot
            )
            if not transcript:
                await interaction.response.send_message("Failed to generate transcript!", ephemeral=True)
                logging.error("[MOD APP] Transcript exporter returned None or Empty string")
                return

            # Ensure transcript is a string
            if isinstance(transcript, bytes):
                transcript = transcript.decode("utf-8")

            logging.info(f"[TICKETTING SYSTEM] Transcript generated: {len(transcript)} characters")
        except Exception as e:
            logging.error(f"[TICKETTING SYSTEM] Failed to generate transcript: {e}")
            transcript = f"<html><body><h1>Error generating transcript</h1><p>{str(e)}</p></body></html>"

        assert isinstance(ticket_creator, discord.Member)

        await self.generate_discord_transcript(
            interaction, transcript, ticket_creator, ticket_created_unix, ticket_closed_unix, mod_app_channel
        )
        await self.generate_discord_transcript(
            interaction, transcript, ticket_creator, ticket_created_unix, ticket_closed_unix, ticket_creator
        )
        assert not isinstance(interaction.channel, discord.DMChannel)
        assert interaction.channel is not None
        await asyncio.sleep(3)
        if not isinstance(interaction.channel, discord.GroupChannel):
            await interaction.channel.delete(reason="Ticket Deleted")
        else:
            raise TypeError("interaction.channel is a GroupChannel?! We can't delete from those!")
        cur.execute("DELETE FROM ticket WHERE discord_id=?", (ticket_creator_id,))
        conn.commit()

    async def generate_discord_transcript(
        self,
        interaction: discord.Interaction,
        transcript: str,
        ticket_creator: discord.Member,
        ticket_created_unix: int,
        ticket_closed_unix: int,
        where_to_send: discord.TextChannel | discord.Member,
    ):
        channel = interaction.channel
        if channel is None or isinstance(channel, discord.DMChannel):
            raise ValueError("CHANNEL IS NONE")
        transcript_bytes_logs = io.BytesIO(transcript.encode("utf-8"))
        transcript_file_logs = discord.File(transcript_bytes_logs, filename=f"transcript-logs-{channel.name}.html")
        transcript_info: discord.Embed | None = None
        try:
            transcript_info = discord.Embed(title=f"Ticket Deleted | {channel.name}", color=discord.colour.Color.blue())
            transcript_info.add_field(name="ID", value=id, inline=True)
            if ticket_creator:
                transcript_info.add_field(name="Opened by", value=ticket_creator.mention, inline=True)
            transcript_info.add_field(name="Closed by", value=interaction.user.mention, inline=True)
            transcript_info.add_field(name="Ticket Created", value=f"<t:{ticket_created_unix}:f>", inline=True)
            transcript_info.add_field(name="Ticket Closed", value=f"<t:{ticket_closed_unix}:f>", inline=True)
            await where_to_send.send(
                content="Here's your transcript: \n In order to view it you will have to download the file and open it in your web browser!",  # noqa: E501
                embed=transcript_info,
                file=transcript_file_logs,
            )
        except Exception as e:
            logging.error(f"Failed to send transcript to log channel: {e}")

    def convert_to_unix_timestamp(self, date_string):
        date_format = r"%Y-%m-%d %H:%M:%S"
        dt_obj: datetime = datetime.strptime(date_string, date_format)
        return int(dt_obj.timestamp())
