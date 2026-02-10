import logging
import sqlite3

import discord

from ticketingSystem.CloseButton import CloseButton
from ticketingSystem.MyView import MyView, config
from ticketingSystem.TicketOptions import TicketOptions

# ===== LOGGING =====
handler = logging.FileHandler(filename="tickets.log", encoding="utf-8", mode="a")
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(handler)

# ===== DATA BASE CONNECTION =====
conn = sqlite3.connect("databases/Ticket_System.db")
cur = conn.cursor()


class TicketSystem:
    def __init__(self, bot: discord.Client):
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
