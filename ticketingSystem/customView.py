import asyncio
import datetime as dt
import sqlite3
from pathlib import Path
from zoneinfo import ZoneInfo

import discord
from discord.ext import commands
from pydantic import ValidationError

from ticketingSystem.CloseButton import CloseButton  # noqa
from utils.ticketing import TicketingConfig

# ===== CONFIG =====
try:
    config = TicketingConfig(Path(r"ticketingSystem/ticketing.yaml"))
except ValidationError as e:
    print("Unable to load config. Inner Exception:\n{e}")
    raise e


class UserSelect(discord.ui.UserSelect):
    def __init__(self, bot: commands.Bot):
        super().__init__(
            placeholder="Select a user...",
            min_values=1,
            max_values=3,
        )
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        selected_users = self.values
        await self.open_ticket(interaction, selected_users)

    async def open_ticket(self, interaction: discord.Interaction, users: list[discord.Member | discord.User]):
        guild = interaction.guild
        assert guild
        conn = sqlite3.connect("databases/Ticket_System.db")
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO ticket (discord_name, discord_id, ticket_created, ticket_type) VALUES (?, ?, ?, ?)",
            (
                interaction.user.name,
                interaction.user.id,
                dt.datetime.now(ZoneInfo("America/Chicago")).strftime(r"%Y-%m-%d %H:%M:%S"),
                "mod mail",
            ),
        )
        conn.commit()
        await asyncio.sleep(1)

        cur.execute("SELECT id FROM ticket WHERE discord_id=?", (interaction.user.id,))
        ticket_number = cur.fetchone()[0]

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }

        for user in users:
            overwrites[user] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        guild_name = config.guilds[guild.id]
        categories = config.categories[guild_name]
        category = self.bot.get_channel(categories["mod mail"])
        assert isinstance(category, discord.CategoryChannel)

        names = "-".join(u.name for u in users)
        channel = await guild.create_text_channel(
            name=f"ticket-{names}"[:100],  # To avoid limit issues
            overwrites=overwrites,
            category=category,
        )

        await interaction.followup.send(
            f"Ticket created: {channel.mention}",
            ephemeral=True,
        )

        embed = discord.Embed(
            description=f"Welcome {interaction.user.mention}, now you can contact them",  # ticket welcome message
            color=discord.colour.Color.blue(),
        )
        await channel.send(embed=embed, view=CloseButton(bot=self.bot))
        cur.execute("UPDATE ticket SET ticket_channel = ? WHERE id = ?", (channel.id, ticket_number))
        conn.commit()


class PickerView(discord.ui.View):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.add_item(UserSelect(bot))


class customView(discord.ui.View):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        super().__init__(timeout=None)

    @discord.ui.button(label="Add users", custom_id="add_users_btn", style=discord.ButtonStyle.blurple)
    async def add_users(self, interaction: discord.Interaction, btn: discord.ui.Button):
        await interaction.response.send_message("Select users:", view=PickerView(self.bot), ephemeral=True)
