cd ~/ROOTGHOST
cat > commands/hola.py <<'PY'
import discord
from discord import app_commands
from discord.ext import commands


class Hola(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="hola",
        description="Saluda desde ROOTGHOST."
    )
    async def hola(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="👻 ROOTGHOST",
            description=(
                f"¡Hola, {interaction.user.mention}!\n\n"
                "El sistema está activo y listo para operar."
            ),
            color=discord.Color.from_rgb(0, 255, 100)
        )
        embed.set_footer(text="ROOTGHOST // SYSTEM ONLINE")

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Hola(bot))
PY