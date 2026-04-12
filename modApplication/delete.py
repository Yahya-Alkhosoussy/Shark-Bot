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
    config = TicketingConfig(Path(r"modApplication/config.yaml"))
except ValidationError as e:
    logging.critical(f"[MOD APPLICATION] Unable to load config {e}")
    raise e
timezone = ZoneInfo("America/Chicago")

conn = sqlite3.connect("databases/mod_applications.db")
cur = conn.cursor()


class delete(discord.ui.View):
    def __init__(self, bot: discord.Client):
        self.bot = bot
        super().__init__(timeout=None)

    @discord.ui.button(label="Delete application", style=discord.ButtonStyle.blurple, custom_id="retract")
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):

        # RESPOND IMMEDIATELY
        embed = discord.Embed(description="⏳ deleting application...", color=0xFF0000)
        await interaction.response.send_message(embed=embed)

        channel_id = interaction.channel.id if interaction.channel else None
        cur.execute("SELECT id, discord_id, ticket_created FROM application WHERE ticket_channel=?", (channel_id,))
        app_data = cur.fetchone()
        if app_data is None:
            logging.warning("[TICKETING SYSTEM] app_data is None")
            return
        id, ticket_creator_id, ticket_created = app_data
        assert not isinstance(interaction.channel, discord.DMChannel)
        assert interaction.channel is not None
        await asyncio.sleep(3)
        if not isinstance(interaction.channel, discord.GroupChannel):
            await interaction.channel.delete(reason="Ticket Deleted")
        else:
            raise TypeError("interaction.channel is a GroupChannel?! We can't delete from those!")
        cur.execute("DELETE FROM application WHERE discord_id=?", (ticket_creator_id,))
        conn.commit()

    def convert_to_unix_timestamp(self, date_string):
        date_format = r"%Y-%m-%d %H:%M:%S"
        dt_obj: datetime = datetime.strptime(date_string, date_format)
        return int(dt_obj.timestamp())
