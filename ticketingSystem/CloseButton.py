import discord

from ticketingSystem.TicketOptions import TicketOptions


# First button for the ticket
class CloseButton(discord.ui.View):
    def __init__(self, bot: discord.Client, send_dm: bool | None = None):
        self.bot = bot
        self.send_dm = send_dm
        super().__init__(timeout=None)

    @discord.ui.button(label="Delete Ticket 🎫", style=discord.ButtonStyle.blurple, custom_id="close")
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="Delete Ticket 🎫",
            description="Are you sure you want to delete this Ticket?",
            color=discord.colour.Color.green(),
        )
        await interaction.response.send_message(
            embed=embed, view=TicketOptions(bot=self.bot, send_dm=self.send_dm)
        )  # This wil show the user the Ticket Options view
        assert interaction.message
        await interaction.message.edit(view=self)
