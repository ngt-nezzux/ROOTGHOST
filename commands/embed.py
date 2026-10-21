
import re

import discord
from discord import app_commands
from discord.ext import commands


def color_hexadecimal(valor: str) -> discord.Color:
    valor = valor.strip().removeprefix("#")

    if not re.fullmatch(r"[0-9a-fA-F]{6}", valor):
        raise ValueError(
            "El color debe ser hexadecimal de 6 dígitos, "
            "por ejemplo #5865F2."
        )

    return discord.Color(int(valor, 16))


class EmbedPersonalizado(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="embed",
        description="Crea un embed personalizado"
    )
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.describe(
        titulo="Título del embed",
        descripcion="Contenido principal del embed",
        color="Color hexadecimal, por ejemplo #5865F2",
        pie="Texto pequeño al pie del embed (opcional)",
        imagen="URL pública de una imagen (opcional)"
    )
    async def embed(
        self,
        interaction: discord.Interaction,
        titulo: app_commands.Range[str, 1, 256],
        descripcion: app_commands.Range[str, 1, 4000],
        color: str = "#5865F2",
        pie: app_commands.Range[str, 1, 2048] = None,
        imagen: str = None
    ):
        try:
            embed_color = color_hexadecimal(color)
        except ValueError as error:
            await interaction.response.send_message(
                f"❌ {error}",
                ephemeral=True
            )
            return

        if imagen:
            if (
                not imagen.startswith(("https://", "http://"))
                or any(char.isspace() for char in imagen)
            ):
                await interaction.response.send_message(
                    "❌ La imagen debe tener una URL HTTP o HTTPS válida.",
                    ephemeral=True
                )
                return

        embed = discord.Embed(
            title=titulo,
            description=descripcion,
            color=embed_color
        )

        if pie:
            embed.set_footer(
                text=f"{pie} • ROOTGHOST"
            )
        else:
            embed.set_footer(text="ROOTGHOST SECURITY SYSTEM")

        if imagen:
            embed.set_image(url=imagen)

        await interaction.response.send_message(
            embed=embed,
            allowed_mentions=discord.AllowedMentions.none()
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(EmbedPersonalizado(bot))
