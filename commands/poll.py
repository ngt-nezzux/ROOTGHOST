
import discord
from discord import app_commands
from discord.ext import commands


EMOJIS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]


class Poll(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="poll",
        description="Crea una encuesta con hasta cuatro opciones."
    )
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.describe(
        pregunta="Pregunta de la encuesta.",
        opcion1="Primera opción.",
        opcion2="Segunda opción.",
        opcion3="Tercera opción, opcional.",
        opcion4="Cuarta opción, opcional."
    )
    async def poll(
        self,
        interaction: discord.Interaction,
        pregunta: str,
        opcion1: str,
        opcion2: str,
        opcion3: str = None,
        opcion4: str = None
    ):
        opciones = [
            opcion.strip()
            for opcion in [opcion1, opcion2, opcion3, opcion4]
            if opcion and opcion.strip()
        ]

        if len(pregunta.strip()) < 3 or len(pregunta) > 250:
            await interaction.response.send_message(
                "La pregunta debe tener entre 3 y 250 caracteres.",
                ephemeral=True
            )
            return

        if any(len(opcion) > 100 for opcion in opciones):
            await interaction.response.send_message(
                "Cada opción puede tener hasta 100 caracteres.",
                ephemeral=True
            )
            return

        if len(opciones) < 2:
            await interaction.response.send_message(
                "La encuesta necesita al menos dos opciones.",
                ephemeral=True
            )
            return

        if len({opcion.casefold() for opcion in opciones}) != len(opciones):
            await interaction.response.send_message(
                "No podés repetir opciones en la misma encuesta.",
                ephemeral=True
            )
            return

        if not interaction.app_permissions.send_messages:
            await interaction.response.send_message(
                "ROOTGHOST necesita permiso para enviar mensajes.",
                ephemeral=True
            )
            return

        if not interaction.app_permissions.add_reactions:
            await interaction.response.send_message(
                "ROOTGHOST necesita permiso para añadir reacciones.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="ROOTGHOST // COMMUNITY POLL",
            description=f"**{pregunta.strip()}**",
            color=0x5865F2,
            timestamp=discord.utils.utcnow()
        )

        for indice, opcion in enumerate(opciones):
            embed.add_field(
                name=f"{EMOJIS[indice]} Opción {indice + 1}",
                value=opcion,
                inline=False
            )

        embed.set_footer(
            text=f"Encuesta creada por {interaction.user.display_name}"
        )

        await interaction.response.defer(ephemeral=True, thinking=True)

        try:
            mensaje = await interaction.channel.send(
                embed=embed,
                allowed_mentions=discord.AllowedMentions.none()
            )

            for emoji in EMOJIS[:len(opciones)]:
                await mensaje.add_reaction(emoji)

            await interaction.followup.send(
                "Encuesta publicada correctamente.",
                ephemeral=True
            )

        except discord.Forbidden:
            await interaction.followup.send(
                "No tengo permisos para publicar la encuesta "
                "o añadir sus reacciones.",
                ephemeral=True
            )
        except discord.HTTPException:
            await interaction.followup.send(
                "Ocurrió un error al publicar la encuesta. "
                "Revisá el canal e intentá nuevamente.",
                ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Poll(bot))
