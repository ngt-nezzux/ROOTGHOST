
import discord
from discord import app_commands
from discord.ext import commands


EMOJIS_ENCUESTA = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]


class PollResults(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="poll-results",
        description="Consultar los resultados de una encuesta de ROOTGHOST."
    )
    @app_commands.guild_only()
    @app_commands.describe(
        canal="Canal donde está publicada la encuesta.",
        mensaje_id="ID del mensaje de la encuesta."
    )
    @app_commands.checks.has_permissions(manage_messages=True)
    async def poll_results(
        self,
        interaction: discord.Interaction,
        canal: discord.TextChannel,
        mensaje_id: str
    ):
        if not mensaje_id.isdigit():
            await interaction.response.send_message(
                "❌ El ID del mensaje debe contener solo números.",
                ephemeral=True
            )
            return

        if canal.guild.id != interaction.guild_id:
            await interaction.response.send_message(
                "❌ El canal debe pertenecer a este servidor.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True, thinking=True)

        try:
            mensaje = await canal.fetch_message(int(mensaje_id))
        except discord.NotFound:
            await interaction.followup.send(
                "❌ No encontré ese mensaje en el canal indicado.",
                ephemeral=True
            )
            return
        except discord.Forbidden:
            await interaction.followup.send(
                "❌ No tengo permisos para leer ese mensaje. "
                "Revisá Ver canal y Leer historial de mensajes.",
                ephemeral=True
            )
            return
        except discord.HTTPException:
            await interaction.followup.send(
                "❌ Discord no permitió consultar el mensaje. "
                "Intentá nuevamente.",
                ephemeral=True
            )
            return

        if not mensaje.embeds:
            await interaction.followup.send(
                "❌ Ese mensaje no contiene una encuesta de ROOTGHOST.",
                ephemeral=True
            )
            return

        encuesta = mensaje.embeds[0]

        if encuesta.title != "ROOTGHOST // COMMUNITY POLL":
            await interaction.followup.send(
                "❌ El mensaje no parece ser una encuesta creada "
                "con el comando /poll de ROOTGHOST.",
                ephemeral=True
            )
            return

        resultados = discord.Embed(
            title="ROOTGHOST // POLL RESULTS",
            description=encuesta.description or "Resultados de la encuesta",
            color=0x5865F2,
            timestamp=discord.utils.utcnow()
        )

        total_votos = 0

        for emoji in EMOJIS_ENCUESTA:
            reaccion = discord.utils.get(mensaje.reactions, emoji=emoji)

            if reaccion is None:
                continue

            # Excluir la reacción del propio bot del total.
            votos = max(0, reaccion.count - int(reaccion.me))
            total_votos += votos

            opcion = next(
                (
                    campo.value
                    for campo in encuesta.fields
                    if campo.name.startswith(emoji)
                ),
                "Opción no identificada"
            )

            resultados.add_field(
                name=f"{emoji} {opcion[:200]}",
                value=f"Votos registrados: **{votos}**",
                inline=False
            )

        resultados.add_field(
            name="Total de votos",
            value=f"**{total_votos}**",
            inline=False
        )

        resultados.set_footer(text="ROOTGHOST SECURITY SYSTEM")

        await interaction.followup.send(
            embed=resultados,
            ephemeral=True,
            allowed_mentions=discord.AllowedMentions.none()
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(PollResults(bot))
