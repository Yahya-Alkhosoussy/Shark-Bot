import logging
import sqlite3

import discord

from modApplication.CloseButton import CloseButton
from modApplication.delete import delete
from modApplication.MyView import MyView, config
from modApplication.submit import submit

conn = sqlite3.connect("databases/mod_applications.db")
cur = conn.cursor()


class ApplicationSystem:
    def __init__(self, bot: discord.Client):
        self.bot = bot

        cur.execute(
            """CREATE TABLE IF NOT EXISTS applications
            (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                discord_name TEXT NOT NULL,
                discord_id INTEGER NOT NULL,
                ticket_created TEXT NOT NULL,
                ticket_channel INTEGER
            )"""
        )

    def setup_hook(self):
        self.bot.add_view(MyView(bot=self.bot))
        self.bot.add_view(CloseButton(bot=self.bot))
        self.bot.add_view(submit(bot=self.bot))
        self.bot.add_view(delete(bot=self.bot))
        print("MOD APP SYSTEM LOADED")

    async def send_ticket_panel(self, channel: discord.TextChannel):
        embed = discord.Embed(
            title="Mod Applications",
            description="This is where you can apply to be a mod",
            color=discord.colour.Color.blue(),
        )
        message = await channel.send(embed=embed, view=MyView(bot=self.bot))
        logging.info("[MOD APPLICATION] mod app sent")
        guild_name = config.guilds[channel.guild.id]
        config.save_message_id(guild_name, message.id)
