import discord

from modApplication.delete import delete
from modApplication.submit import submit


# buttons for the ticket
class CloseButton(discord.ui.View):
    def __init__(self, bot: discord.Client):
        self.bot = bot
        super().__init__(timeout=None)

    @discord.ui.button(label="Submit Application ✅", style=discord.ButtonStyle.blurple, custom_id="submition")
    async def submit(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="Submit Application ✅",
            description="Are you sure you want to submit the application?",
            color=discord.colour.Color.green(),
        )
        await interaction.response.send_message(embed=embed, view=submit(bot=self.bot))
        assert interaction.message
        await interaction.message.edit(view=self)

    @discord.ui.button(label="Delete Application ❌", style=discord.ButtonStyle.red, custom_id="deletion")
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="Delete Application ❌",
            description="Are you sure you want to delete the application?",
            color=discord.colour.Color.green(),
        )
        await interaction.response.send_message(embed=embed, view=delete(bot=self.bot))
        assert interaction.message
        await interaction.message.edit(view=self)
