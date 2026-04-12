import asyncio
import datetime as dt
import logging
import sqlite3
from pathlib import Path
from zoneinfo import ZoneInfo

import discord
from pydantic import ValidationError

from modApplication.CloseButton import CloseButton
from modApplication.ModQuestions import ModQuestions
from utils.ticketing import TicketingConfig

try:
    config = TicketingConfig(Path(r"modApplication/config.yaml"))
except ValidationError as e:
    logging.critical(f"Unable to load config: {e}")
    raise e

timezone = ZoneInfo("America/Chicago")

conn = sqlite3.connect("databases/mod_applications.db")
cur = conn.cursor()


class MyView(discord.ui.View):
    def __init__(self, bot: discord.Client):
        super().__init__(timeout=None)
        self.bot = bot
        self.mod_questions = ModQuestions(bot=self.bot, channel=None)

    @discord.ui.button(label="Apply", style=discord.ButtonStyle.blurple, custom_id="mod_app_button")
    async def callback(self, interaction: discord.Interaction, button: discord.ui.Button):

        button.disabled = True
        await interaction.response.edit_message(view=self)

        creation_date = dt.datetime.now(timezone).strftime(r"%Y-%m-%d %H:%M:%S")
        user_name = interaction.user.name
        user_id = interaction.user.id

        guild_ids: list[int] = []
        for guild in config.guilds:
            guild_ids.append(guild[1][2])

        if interaction.guild and interaction.guild.id in guild_ids:
            guild_id = interaction.guild.id
        else:
            logging.warning("⚠️ [TICKETS] Guild id is not in config. ⚠️")
            return

        guild_name = config.guilds[guild_id]
        # Check if the user already has a ticket
        cur.execute("SELECT id FROM application WHERE discord_id=?", (user_id,))
        existing_ticket = cur.fetchone()

        if existing_ticket is not None:
            embed = discord.Embed(title="You already have an open application.", color=0xFF0000)  # RGB so it's all RED
            await interaction.followup.send(embed=embed, ephemeral=True)
            await asyncio.sleep(1)
            embed = discord.Embed(
                title="Mod Applications",
                description="This is where you can apply to be a mod",
                color=discord.colour.Color.blue(),
            )
            assert interaction.message
            await interaction.message.edit(
                embed=embed, view=MyView(bot=self.bot)
            )  # This will reset the SelectMenu in the ticket channel
        guild = self.bot.get_guild(guild_id)
        assert guild
        category_ids = config.categories[guild_name]

        role_ids = config.roles[guild_name]
        mod_role = guild.get_role(role_ids["mods"])

        if interaction.data:
            if interaction.channel and interaction.channel.id == config.ticket_channels[guild_name]:
                cur.execute(
                    "INSERT INTO application (discord_name, discord_id, ticket_created) VALUES (?, ?, ?)",
                    (user_name, user_id, creation_date),
                )
                conn.commit()
                await asyncio.sleep(1)

                cur.execute("SELECT id FROM application WHERE discord_id=?", (user_id,))
                ticket_number = cur.fetchone()[0]
                category = self.bot.get_channel(category_ids["mod app"])

                if isinstance(category, discord.CategoryChannel):
                    ticket_channel = await guild.create_text_channel(
                        f"mod application-{ticket_number}", category=category, topic=f"{interaction.user.id}"
                    )
                else:
                    raise TypeError(f"category channel is {type(category)}, which is not a ChannelCategory type as required!")

                if mod_role:
                    await ticket_channel.set_permissions(
                        mod_role,
                        send_messages=True,
                        read_messages=True,
                        add_reactions=True,  # set permissions for the staff team
                        embed_links=True,
                        attach_files=True,
                        read_message_history=True,
                        external_emojis=True,
                    )
                else:
                    raise KeyError(
                        f"Could not get role from guild for roleId {role_ids['mods']}. Cannot set MODS staff role permissions!"  # noqa: E501
                    )

                if isinstance(interaction.user, discord.Member):
                    await ticket_channel.set_permissions(
                        interaction.user,
                        send_messages=True,
                        read_messages=True,
                        add_reactions=False,  # Set the permissions for the user
                        embed_links=True,
                        attach_files=True,
                        read_message_history=True,
                        external_emojis=True,
                    )
                else:
                    raise TypeError("interaction.user is not Member type! Cannot set user permissions")

                await ticket_channel.set_permissions(
                    guild.default_role, send_messages=False, read_messages=False, view_channel=False
                )
                embed = discord.Embed(
                    description=f"Welcome {interaction.user.mention}, \n please follow the directions given by the bot",  # ticket welcome message  # noqa: E501
                    color=discord.colour.Color.blue(),
                )
                await ticket_channel.send(embed=embed, view=CloseButton(bot=self.bot))

                channel_id = ticket_channel.id
                cur.execute("UPDATE application SET ticket_channel = ? WHERE id = ?", (channel_id, ticket_number))
                conn.commit()
                embed = discord.Embed(
                    description=f"📬 application was created! Look here --> {ticket_channel.mention}",
                    color=discord.colour.Color.green(),
                )

                await interaction.followup.send(embed=embed, ephemeral=True)
                await asyncio.sleep(1)
                embed = discord.Embed(
                    title="Mod Applications",
                    description="This is where you can apply to be a mod",
                    color=discord.colour.Color.blue(),
                )
                assert interaction.message
                await interaction.message.edit(embed=embed, view=MyView(bot=self.bot))  # This will reset the select menu
                await self.mod_questions.send_questions(channel=ticket_channel, author=interaction.user)
                # Re-enable after a delay
                await asyncio.sleep(3)
                button.disabled = False
                await interaction.message.edit(view=self)  # re-enable it on the embed
