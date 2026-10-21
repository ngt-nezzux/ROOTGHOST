
import discord
from discord import app_commands
from discord.ext import commands


class Ayuda(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="ayuda",
        description="Muestra información de ROOTGHOST"
    )
    async def ayuda(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "**ROOTGHOST // CENTRO DE AYUDA**\n\n"
            "`/hola` — Saluda al usuario.\n"
            "`/ping` — Comprueba la latencia.\n"
            "`/ayuda` — Muestra este mensaje.",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Ayuda(bot))
