
cd ~/ROOTGHOST
mkdir -p commands

cat > commands/poll_results.py <<'PY'
import discord
from discord import app_commands
from discord.ext import commands


EMOJIS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]


class PollResults(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="poll-results",
        description="Consultar los resultados de una encuesta."
    )
    @app_commands.guild_only()
    @app_commands.describe(
        mensaje_id="ID del mensaje de la encuesta."
    )
    async def poll_results(
        self,
        interaction: discord.Interaction,
        mensaje_id: str
    ):
        if not mensaje_id.isdigit():
            return await interaction.response.send_message(
                "El ID del mensaje debe contener solo números.",
                ephemeral=True
            )

        if not interaction.channel:
            return await interaction.response.send_message(
                "No pude identificar el canal.",
                ephemeral=True
            )

        try:
            message = await interaction.channel.fetch_message(
                int(mensaje_id)
            )
        except discord.NotFound:
            return await interaction.response.send_message(
                "No encontré ese mensaje en este canal.",
                ephemeral=True
            )
        except discord.Forbidden:
            return await interaction.response.send_message(
                "No tengo permiso para leer el mensaje.",
                ephemeral=True
            )
        except discord.HTTPException:
            return await interaction.response.send_message(
                "No pude consultar el mensaje. Intentá nuevamente.",
                ephemeral=True
            )

        if not message.embeds:
            return await interaction.response.send_message(
                "Ese mensaje no contiene un embed de encuesta.",
                ephemeral=True
            )

        embed_original = message.embeds[0]

        if not embed_original.title or "COMMUNITY POLL" not in embed_original.title:
            return await interaction.response.send_message(
                "Ese mensaje no parece ser una encuesta de ROOTGHOST.",
                ephemeral=True
            )

        resultado = discord.Embed(
            title="ROOTGHOST // POLL RESULTS",
            description=embed_original.description or "Encuesta",
            color=0x5865F2
        )

        total_votos = 0

        for emoji in EMOJIS:
            reaccion = discord.utils.get(
                message.reactions,
                emoji=emoji
            )

            if reaccion is None:
                continue

            votos = max(0, reaccion.count - (1 if reaccion.me else 0))
            total_votos += votos

            opcion = next(
                (
                    campo.value
                    for campo in embed_original.fields
                    if campo.name.startswith(emoji)
                ),
                "Opción"
            )

            resultado.add_field(
                name=f"{emoji} {opcion[:200]}",
                value=f"**{votos}** voto(s)",
                inline=False
            )

        resultado.set_footer(
            text=f"Total de votos registrados: {total_votos}"
        )

        await interaction.response.send_message(
            embed=resultado,
            ephemeral=True,
            allowed_mentions=discord.AllowedMentions.none()
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(PollResults(bot))
PY

python -m py_compile commands/poll_results.py
