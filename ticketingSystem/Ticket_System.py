import logging
import sqlite3

import discord
from discord.ext import commands

from ticketingSystem.CloseButton import CloseButton
from ticketingSystem.customView import customView
from ticketingSystem.MyView import MyView, config
from ticketingSystem.TicketOptions import TicketOptions
from utils.ticketing import TicketingConfig

# ===== LOGGING =====
handler = logging.FileHandler(filename="tickets.log", encoding="utf-8", mode="a")
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(handler)

# ===== DATA BASE CONNECTION =====
conn = sqlite3.connect("databases/Ticket_System.db")
cur = conn.cursor()


class TicketSystem:
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        cur.execute("""CREATE TABLE IF NOT EXISTS 'ticket' (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    discord_name TEXT NOT NULL,
                    discord_id INTEGER NOT NULL,
                    ticket_created TEXT NOT NULL,
                    ticket_channel INTEGER,
                    ticket_type TEXT
            );""")

        # Maybe used later
        cur.execute("""CREATE TABLE IF NOT EXISTS 'ticket history'(
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        ticket_id INTEGER NOT NULL,
                        discord_name TEXT NOT NULL,
                        discord_id INTEGER NOT NULL,
                        ticket_created TEXT NOT NULL,
                        ticket_closed TEXT,
                        closed_by_id INTEGER,
                        ticket_type TEXT,
                        transcript_saved BOOLEAN DEFAULT 0
                    );""")

    async def setup_hook(self):
        """
        Docstring for setup_hook

        :param self: Description
        """
        # Register the persistence views
        self.bot.add_view(MyView(bot=self.bot))
        self.bot.add_view(CloseButton(bot=self.bot))
        self.bot.add_view(TicketOptions(bot=self.bot))
        self.bot.add_view(customView(bot=self.bot))
        print("Ticket system loaded | Ticket_System.py")

    async def send_ticket_panel(self, channel: discord.TextChannel):
        """
        Docstring for send_ticket_panel

        :param self:
        """

        embed = discord.Embed(
            title="Support ticket",
            description="This is where you can raise a ticket for tech support or access mod mail",
            colour=discord.colour.Color.blue(),
        )

        message = await channel.send(embed=embed, view=MyView(bot=self.bot))
        logging.info("[TICKETING SYSTEM] Support Ticket Sent")
        guild_name = config.guilds[channel.guild.id]
        config.save_message_id(guild_name, message.id)

    async def send_custom_ticket_panel(self, channel: discord.TextChannel, ticket_config: TicketingConfig):

        embed = discord.Embed(
            title="Open a custom mod ticket",
            description="This is where u can open a ticket with certain people",
            colour=discord.colour.Color.blue(),
        )
        message = await channel.send(embed=embed, view=customView(self.bot))
        guild_name = config.guilds[channel.guild.id]
        ticket_config.save_message_id(guild_name, message.id, True)

    async def check_for_ticket(self, ticket_config: TicketingConfig, guild_name: str, guild: discord.Guild):
        print("set up not done")

        logging.info("[TICKETING SYSTEM] Ticket system set up, checking for messages now")

        embed_message_ids = ticket_config.embed_messages
        if embed_message_ids and embed_message_ids[guild_name] == 0:
            channel_id = ticket_config.ticket_channels[guild_name]
            if channel_id is not None or channel_id != 0:
                channel = guild.get_channel(channel_id)
                if channel and isinstance(channel, discord.TextChannel):
                    await self.send_ticket_panel(channel=channel)
                else:
                    logging.warning(f"[TICKET SYSTEM] Channel {channel_id} does not exist or is not a TextChannel")
                    return
            else:
                logging.warning(f"[TICKET SYSTEM] Channel ID for {guild_name} is either None or Zero!")
                return

            logging.info(f"[TICKETING SYSTEM] Ticket embed sent to {guild_name}")

    async def check_for_custom_ticket(self, ticket_config: TicketingConfig, guild_name: str, guild: discord.Guild):
        print("set up not done")

        logging.info("[TICKETING SYSTEM] Ticket system set up, checking for messages now")

        embed_message_ids = ticket_config.custom_embed_messages
        if embed_message_ids and embed_message_ids[guild_name] == 0:
            channel_id = ticket_config.custom_ticket_channels[guild_name]
            if channel_id is not None or channel_id != 0:
                channel = guild.get_channel(channel_id)
                if channel and isinstance(channel, discord.TextChannel):
                    await self.send_custom_ticket_panel(channel=channel, ticket_config=ticket_config)
                else:
                    logging.warning(f"[TICKET SYSTEM] Channel {channel_id} does not exist or is not a TextChannel")
                    return
            else:
                logging.warning(f"[TICKET SYSTEM] Channel ID for {guild_name} is either None or Zero!")
                return

            logging.info(f"[TICKETING SYSTEM] Ticket embed sent to {guild_name}")
