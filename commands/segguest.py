
import discord
from discord import app_commands
from discord.ext import commands


class SuggestionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.votes = {}

    async def update_vote(self, interaction, vote):
        self.votes[interaction.user.id] = vote

        positive = sum(v == "yes" for v in self.votes.values())
        negative = sum(v == "no" for v in self.votes.values())

        embed = interaction.message.embeds[0]
        embed.set_field_at(
            1, name="A favor", value=f"👍 {positive}", inline=True
        )
        embed.set_field_at(
            2, name="En contra", value=f"👎 {negative}", inline=True
        )

        await interaction.response.edit_message(
            embed=embed, view=self
        )

    @discord.ui.button(
        label="A favor",
        emoji="👍",
        style=discord.ButtonStyle.success,
        custom_id="rootghost:suggest:yes"
    )
    async def vote_yes(self, interaction, button):
        await self.update_vote(interaction, "yes")

    @discord.ui.button(
        label="En contra",
        emoji="👎",
        style=discord.ButtonStyle.danger,
        custom_id="rootghost:suggest:no"
    )
    async def vote_no(self, interaction, button):
        await self.update_vote(interaction, "no")


class Suggest(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="suggest",
        description="Publica una sugerencia para el servidor."
    )
    @app_commands.guild_only()
    @app_commands.describe(
        idea="La sugerencia que querés proponer."
    )
    async def suggest(self, interaction: discord.Interaction, idea: str):
        if len(idea) > 1500:
            await interaction.response.send_message(
                "La sugerencia no puede superar los 1500 caracteres.",
                ephemeral=True
            )
            return

        if interaction.guild is None or interaction.channel is None:
            await interaction.response.send_message(
                "Este comando solo se puede usar en un servidor.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="ROOTGHOST // SUGGESTION",
            description=idea,
            color=0x5865F2,
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(
            name="Propuesto por",
            value=interaction.user.mention,
            inline=False
        )
        embed.add_field(
            name="A favor",
            value="👍 0",
            inline=True
        )
        embed.add_field(
            name="En contra",
            value="👎 0",
            inline=True
        )
        embed.set_footer(text="ROOTGHOST SECURITY SYSTEM")

        try:
            await interaction.channel.send(
                embed=embed,
                view=SuggestionView(),
                allowed_mentions=discord.AllowedMentions.none()
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "No tengo permisos para publicar en este canal.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            "Tu sugerencia fue publicada correctamente.",
            ephemeral=True
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Suggest(bot))
