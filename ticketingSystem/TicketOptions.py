import asyncio
import io
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import chat_exporter  # pip install chat-exporter
import discord

import utils.read_Yaml as RY

conn = sqlite3.connect("databases/Ticket_System.db")
cur = conn.cursor()

# ===== CONFIG =====
config = RY.read_config(Path(r"ticketingSystem/ticketing.yaml"))
GUILD_IDS: dict = config["guild ids"]
TICKET_CHANNELS: dict = config["ticket channels"]
CATEGORY_IDS: dict = config["category ids"]
ROLE_IDS: dict = config["role ids"]
EMBED_TITLE: str = config["embed title"]
EMBED_DESCRIPTION: str = config["embed description"]
LOG_CHANNELS: dict = config["log channel"]
timezone = ZoneInfo("America/Chicago")

# ===== LOGGING =====
handler = logging.FileHandler(filename="tickets.log", encoding="utf-8", mode="a")
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(handler)


class TicketOptions(discord.ui.View):
    def __init__(self, bot: discord.Client):
        self.bot = bot
        super().__init__(timeout=None)

    @discord.ui.button(label="Delete Ticket 🎫", style=discord.ButtonStyle.red, custom_id="delete")
    async def delete_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild and interaction.guild.id in GUILD_IDS.values():
            guild_id = interaction.guild.id
        else:
            raise ValueError(
                f"Guild ID {interaction.guild.id if interaction.guild else 'NULL'} not found in GUILD_IDS.values()"
            )

        guild = self.bot.get_guild(guild_id)
        id_to_name: dict = {int(v): k for k, v in config["guild ids"].items()}
        guild_log_channels: dict = LOG_CHANNELS[id_to_name.get(guild_id)]
        tech_channel = self.bot.get_channel(guild_log_channels["tech"])
        if not isinstance(tech_channel, discord.TextChannel):
            raise TypeError("Tech Support channel is not a TextChannel!")
        mod_mail_channel = self.bot.get_channel(guild_log_channels["mod mail"])
        if not isinstance(mod_mail_channel, discord.TextChannel):
            raise TypeError("Mod Mail channel is not a TextChannel!")
        channel_id = interaction.channel.id if interaction.channel else None

        # ===== RESPOND IMMEDIATELY (within the 3 second window discord gives) =====
        embed = discord.Embed(description="⏳ Generating transcript and deleting ticket...", color=0xFF0000)
        await interaction.response.send_message(embed=embed)

        # ===== NOW DO EVERYTHING ELSE =====

        cur.execute("SELECT id, discord_id, ticket_created, ticket_type FROM ticket WHERE ticket_channel=?", (channel_id,))
        ticket_data = cur.fetchone()
        if ticket_data is None:
            logging.warning("[TICKETING SYSTEM] ticket_data is None")
            return

        id, ticket_creator_id, ticket_created, ticket_type = ticket_data
        ticket_creator = guild.get_member(ticket_creator_id) if guild else None
        ticket_created_unix = self.convert_to_unix_timestamp(ticket_created)
        ticket_closed = datetime.now(timezone).strftime(r"%Y-%m-%d %H:%M:%S")
        ticket_closed_unix = self.convert_to_unix_timestamp(ticket_closed)
        try:
            # Creating Transcript
            military_time: bool = True
            transcript = await chat_exporter.export(
                interaction.channel, limit=200, tz_info="America/Chicago", military_time=military_time, bot=self.bot
            )

            if not transcript:
                await interaction.response.send_message("Failed to generate transcript!", ephemeral=True)
                logging.error("[TICKETTING SYSTEM] Transcript exporter returned None or Empty string")
                return
            
            # Ensure transcript is a string
            if isinstance(transcript, bytes):
                transcript = transcript.decode("utf-8")

            logging.info(f"[TICKETTING SYSTEM] Transcript generated: {len(transcript)} characters")

        except Exception as e:
            logging.error(f"[TICKETTING SYSTEM] Failed to generate transcript: {e}")
            transcript = f"<html><body><h1>Error generating transcript</h1><p>{str(e)}</p></body></html>"

        transcript_bytes_user = io.BytesIO(transcript.encode("utf-8"))
        if interaction.channel and not isinstance(interaction.channel, discord.DMChannel):
            transcript_file_user = discord.File(
                transcript_bytes_user, filename=f"transcript-user-{interaction.channel.name}.html"
            )
        else:
            raise TypeError("interaction.channel was a DMChannel which is not allowed when trying to save transcripts")

        """
        This separation is needed due to the nature of how BytesIO works.
        After finishing the discord.File it's at the end of the Bytes, so the next file will result in having 0 Bytes of data.
        """

        transcript_bytes_logs = io.BytesIO(transcript.encode("utf-8"))
        transcript_file_logs = discord.File(transcript_bytes_logs, filename=f"transcript-logs-{interaction.channel.name}.html")
        transcript_info: discord.Embed | None = None

        try:
            transcript_info = discord.Embed(
                title=f"Ticket Deleted | {interaction.channel.name}", color=discord.colour.Color.blue()
            )
            transcript_info.add_field(name="ID", value=id, inline=True)
            if ticket_creator:
                transcript_info.add_field(name="Opened by", value=ticket_creator.mention, inline=True)
            transcript_info.add_field(name="Closed by", value=interaction.user.mention, inline=True)
            transcript_info.add_field(name="Ticket Created", value=f"<t:{ticket_created_unix}:f>", inline=True)
            transcript_info.add_field(name="Ticket Closed", value=f"<t:{ticket_closed_unix}:f>", inline=True)
            if ticket_type == "mod mail":
                await mod_mail_channel.send(
                    content="Here's your transcript: \n In order to view it you will have to download the file and open it in your web browser!",
                    embed=transcript_info,
                    file=transcript_file_logs,
                )
            elif ticket_type == "tech support":
                await tech_channel.send(
                    content="Here's your transcript: \n In order to view it you will have to download the file and open it in your web browser!",
                    embed=transcript_info,
                    file=transcript_file_logs,
                )
        except Exception as e:
            logging.error(f"Failed to send transcript to log channel: {e}")

        if ticket_creator:
            try:
                # Create a copy of the embed for DM
                dm_embed = discord.Embed(
                    title=f"Ticket Deleted | {interaction.channel.name}", color=discord.colour.Color.blue()
                )
                dm_embed.add_field(name="ID", value=id, inline=True)
                dm_embed.add_field(name="Opened by", value=ticket_creator.mention, inline=True)
                dm_embed.add_field(name="Closed by", value=interaction.user.mention, inline=True)
                dm_embed.add_field(name="Ticket Created", value=f"<t:{ticket_created_unix}:f>", inline=True)
                dm_embed.add_field(name="Ticket Closed", value=f"<t:{ticket_closed_unix}:f>", inline=True)

                await ticket_creator.send(
                    content="Here's your transcript: \n In order to view it you will have to download the file and open it in your web browser!",
                    embed=dm_embed,
                    file=transcript_file_user,
                )
            except Exception as e:
                logging.error(f"Failed to send DM to ticket creator ({ticket_creator}): {e}")

        await asyncio.sleep(3)
        if not isinstance(interaction.channel, discord.GroupChannel):
            await interaction.channel.delete(reason="Ticket Deleted")
        else:
            raise TypeError("interaction.channel is a GroupChannel?! We can't delete from those!")
        cur.execute("DELETE FROM ticket WHERE discord_id=?", (ticket_creator_id,))
        conn.commit()

    def convert_to_unix_timestamp(self, date_string):
        date_format = r"%Y-%m-%d %H:%M:%S"
        dt_obj: datetime = datetime.strptime(date_string, date_format)
        return int(dt_obj.timestamp())
