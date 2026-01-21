import discord, sqlite3
from pathlib import Path
from zoneinfo import ZoneInfo
import datetime as dt
from utils.read_Yaml import read_config
import asyncio, logging
from ticketingSystem.CloseButton import CloseButton, TicketOptions

# ===== LOGGING =====
handler = logging.FileHandler(filename="tickets.log", encoding="utf-8", mode="a")
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(handler)

conn = sqlite3.connect("databases/Ticket_System.db")
cur = conn.cursor()

# ===== CONFIG =====
config = read_config(Path(r"ticketingSystem\ticketing.yaml"))
GUILD_IDS: dict = config["guild ids"]
TICKET_CHANNELS: dict = config["ticket channels"]
CATEGORY_IDS: dict = config["category ids"]
ROLE_IDS: dict = config["role ids"]
EMBED_TITLE: str = config["embed title"]
EMBED_DESCRIPTION: str = config["embed description"]
LOG_CHANNEL: int = config["log channel"]
timezone = ZoneInfo("America/Chicago")

class MyView(discord.ui.View):
    def __init__(self, bot: discord.Client):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.select(
        custom_id="support",
        placeholder="Choose a Ticket option",
        options=[
            discord.SelectOption(
                label="Mod mail",
                description="Report something to the mods or get help from the mods",
                emoji='📧',
                value="mod mail"
            ),
            discord.SelectOption(
                label="Tech support",
                description="Got a tech related question or issue? Come and ask!",
                emoji='💻',
                value="tech support"
            )
        ]
    )
    async def callback(self, interaction: discord.Interaction, select):
        await interaction.response.defer(ephemeral=True)
        
        creation_date = dt.datetime.now(timezone).strftime(r'%Y-%m-%d %H:%M:%S')
        user_name = interaction.user.name
        user_id = interaction.user.id

        if interaction.guild.id in GUILD_IDS.values():
            guild_id = interaction.guild.id
        else: 
            logging.warning("⚠️ [TICKETS] Guild id is not in config. ⚠️")
            return

        id_to_name: dict = {int(v): k for k, v in GUILD_IDS.items()}
        guild_name = id_to_name.get(guild_id)

        # Check if the user already has a ticket
        cur.execute("SELECT id FROM ticket WHERE discord_id=?", (user_id,))
        existing_ticket = cur.fetchone()

        if existing_ticket is not None:
            embed = discord.Embed(title=f"You already have an open ticket.", color=0xff0000) # RGB so it's all RED
            await interaction.followup.send(embed=embed, ephemeral=True)
            await asyncio.sleep(1)
            embed = discord.Embed(title=EMBED_TITLE, description=EMBED_DESCRIPTION, color=discord.colour.Color.blue())
            await interaction.message.edit(embed=embed, view=MyView(bot=self.bot)) # This will reset the SelectMenu in the ticket channel

        # ---- SUPPORT 1 ----
        if "mod mail" in interaction.data['values']:
            if interaction.channel.id == TICKET_CHANNELS.get(guild_name):
                guild = self.bot.get_guild(guild_id)
                
                cur.execute(
                    "INSERT INTO ticket (discord_name, discord_id, ticket_created, ticket_type) VALUES (?, ?, ?, ?)",
                    (user_name, user_id, creation_date, "mod mail")
                )
                conn.commit()
                await asyncio.sleep(1)

                cur.execute("SELECT id FROM ticket WHERE discord_id=?", (user_id,))
                ticket_number = cur.fetchone()[0]
                category_ids: dict = CATEGORY_IDS.get(guild_name)
                category = self.bot.get_channel(category_ids.get("mod mail"))
                ticket_channel = await guild.create_text_channel(f"mod ticket-{ticket_number}", category=category, topic=f"{interaction.user.id}")

                role_ids = ROLE_IDS.get(guild_name)
                await ticket_channel.set_permissions(guild.get_role(role_ids.get("mods")), send_messages=True, read_messages=True, add_reactions=False, # set permissins for the staff team
                                                        embed_links=True, attach_files=True, read_message_history=True, external_emojis=True)
                await ticket_channel.set_permissions(interaction.user, send_messages=True, read_messages=True, add_reactions=False, #Set the permissions for the user
                                                        embed_links=True, attach_files=True, read_message_history=True, external_emojis=True)
                await ticket_channel.set_permissions(guild.default_role, send_messages=False, read_messages=False, view_channel=False)
                embed = discord.Embed(description=f"Welcome {interaction.user.mention}, \n describe your problem and our Support will help you soon", #ticket welcome message
                                        color=discord.colour.Color.blue())
                await ticket_channel.send(embed=embed, view=CloseButton(bot=self.bot))

                channel_id = ticket_channel.id
                cur.execute("UPDATE ticket SET ticket_channel = ? WHERE id = ?", (channel_id, ticket_number))
                conn.commit()

                embed = discord.Embed(description=f"📬 Ticket was created! Look here --> {ticket_channel.mention}", color=discord.colour.Color.green())

                await interaction.followup.send(embed=embed, ephemeral=True)
                await asyncio.sleep(1)
                embed = discord.Embed(title=EMBED_TITLE, description=EMBED_DESCRIPTION, color=discord.colour.Color.blue())
                await interaction.message.edit(embed=embed, view=MyView(bot=self.bot)) # This will reset the select menu

        if "tech support" in interaction.data['values']:
            if interaction.channel.id == TICKET_CHANNELS.get(guild_name):
                guild = self.bot.get_guild(guild_id)

                cur.execute(
                    "INSERT INTO ticket (discord_name, discord_id, ticket_created, ticket_type) VALUES (?, ?, ?, ?)",
                    (user_name, user_id, creation_date, "tech support")
                )
                conn.commit()
                await asyncio.sleep(1)

                cur.execute("SELECT id FROM ticket WHERE discord_id=?", (user_id,))
                ticket_number = cur.fetchone()[0]
                test_server: dict = CATEGORY_IDS.get("test server")
                category = self.bot.get_channel(test_server.get("tech support"))
                ticket_channel = await guild.create_text_channel(f"tech-support-ticket-{ticket_number}", category=category, topic=f"P{interaction.user.id}")
                
                test_server_role_ids = ROLE_IDS.get("test server")
                await ticket_channel.set_permissions(guild.get_role(test_server_role_ids.get("tech")), send_messages=True, read_messages=True, add_reactions=True, # Set permissions for the staff team
                                                        embed_links=True, attach_files=True, read_message_history=True, external_emojis=True)
                await ticket_channel.set_permissions(interaction.user, send_messages=True, read_messages=True, add_reactions=False, #Set the permissions for the user
                                                        embed_links=True, attach_files=True, read_message_history=True, external_emojis=True)
                await ticket_channel.set_permissions(guild.default_role, send_messages=False, read_message_history=False, read_messages=False, view_channel=False)
                embed = discord.Embed(description=f"Welcome {interaction.user.mention}, \n describe your problem and our Support will help you soon", #ticket welcome message
                                        color=discord.colour.Color.blue())
                await ticket_channel.send(embed=embed, view=CloseButton(bot=self.bot))

                channel_id = ticket_channel.id
                cur.execute("UPDATE ticket SET ticket_channel = ? WHERE id = ?", (channel_id, ticket_number))
                conn.commit()

                embed = discord.Embed(description=f"📬 Ticket was created! Look here --> {ticket_channel.mention}", color=discord.colour.Color.green())

                await interaction.followup.send(embed=embed, ephemeral=True)
                await asyncio.sleep(1)
                embed = discord.Embed(title=EMBED_TITLE, description=EMBED_DESCRIPTION, color=discord.colour.Color.blue())
                await interaction.message.edit(embed=embed, view=MyView(bot=self.bot)) # This will reset the select menu